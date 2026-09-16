"""Durable certificate jobs with FastAPI, PostgreSQL, Redis/Celery, and worker pools.

API: ``uvicorn queue:app``
Workers: ``celery -A queue.celery_app worker --loglevel=INFO --concurrency=4``
Dispatcher: run ``dispatch_outbox`` periodically with Celery Beat (for example,
every 30 seconds) to recover jobs committed while Redis was unavailable.
"""

from __future__ import annotations

import os
import threading
import time
import uuid
import logging
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Generator

import httpx
from celery import Celery
from fastapi import Depends, FastAPI, HTTPException, Request, status
from pydantic import BaseModel
from sqlalchemy import DateTime, ForeignKey, Integer, String, UniqueConstraint, create_engine, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, sessionmaker


DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+psycopg://postgres:postgres@localhost/courses")
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
CERTIFICATE_SERVICE_URL = os.getenv("CERTIFICATE_SERVICE_URL", "")
CERTIFICATE_SERVICE_TOKEN = os.getenv("CERTIFICATE_SERVICE_TOKEN", "")
EMAIL_SERVICE_URL = os.getenv("EMAIL_SERVICE_URL", "")
EMAIL_SERVICE_TOKEN = os.getenv("EMAIL_SERVICE_TOKEN", "")
LOCK_TTL = timedelta(minutes=5)
logger = logging.getLogger(__name__)


class Base(DeclarativeBase):
    pass


class JobState(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    SENT = "sent"
    FAILED = "failed"


class Student(Base):
    __tablename__ = "students"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(200))
    email: Mapped[str] = mapped_column(String(320), unique=True)


class Course(Base):
    __tablename__ = "courses"
    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(200))


class CourseCompletion(Base):
    __tablename__ = "course_completions"
    __table_args__ = (UniqueConstraint("student_id", "course_id", name="uq_completion_student_course"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("students.id"), index=True)
    course_id: Mapped[int] = mapped_column(ForeignKey("courses.id"), index=True)
    completed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


class CertificateJob(Base):
    __tablename__ = "certificate_jobs"
    __table_args__ = (UniqueConstraint("completion_id", name="uq_certificate_job_completion"),)
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    completion_id: Mapped[int] = mapped_column(ForeignKey("course_completions.id"), index=True)
    state: Mapped[JobState] = mapped_column(default=JobState.PENDING, index=True)
    attempts: Mapped[int] = mapped_column(Integer, default=0)
    certificate_url: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    locked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_error: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class OutboxEvent(Base):
    __tablename__ = "outbox_events"
    __table_args__ = (UniqueConstraint("certificate_job_id", name="uq_outbox_certificate_job"),)
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    certificate_job_id: Mapped[str] = mapped_column(ForeignKey("certificate_jobs.id"), index=True)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


class TokenBucket:
    """Per-process admission control; deploy a shared gateway limiter when scaling out."""

    def __init__(self, capacity: int = 30, refill_per_second: float = 0.5) -> None:
        self.capacity, self.refill_per_second = capacity, refill_per_second
        self.buckets: dict[str, tuple[float, float]] = {}
        self.lock = threading.Lock()

    def consume(self, key: str) -> bool:
        with self.lock:
            now = time.monotonic()
            tokens, updated = self.buckets.get(key, (float(self.capacity), now))
            tokens = min(self.capacity, tokens + (now - updated) * self.refill_per_second)
            self.buckets[key] = (tokens - 1, now) if tokens >= 1 else (tokens, now)
            return tokens >= 1


limiter = TokenBucket()
engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(engine, expire_on_commit=False)
celery_app = Celery("certificate_jobs", broker=REDIS_URL, backend=REDIS_URL)
# ACK occurs only after a task returns; a worker lost mid-task causes redelivery.
celery_app.conf.update(task_acks_late=True, task_reject_on_worker_lost=True, worker_prefetch_multiplier=1)
app = FastAPI(title="Certificate job system")


class CompletionRequest(BaseModel):
    student_id: int
    course_id: int


class JobResponse(BaseModel):
    job_id: str
    state: JobState


def get_session() -> Generator[Session, None, None]:
    with SessionLocal() as session:
        yield session


def rate_limit(request: Request) -> None:
    key = request.client.host if request.client else "unknown"
    if not limiter.consume(key):
        raise HTTPException(status_code=429, detail="Too many requests")


@app.on_event("startup")
def create_tables() -> None:
    Base.metadata.create_all(engine)


@app.post("/completions", response_model=JobResponse, status_code=status.HTTP_202_ACCEPTED)
def complete_course(data: CompletionRequest, request: Request, session: Session = Depends(get_session)) -> JobResponse:
    rate_limit(request)
    if session.get(Student, data.student_id) is None or session.get(Course, data.course_id) is None:
        raise HTTPException(status_code=404, detail="Student or course not found")

    # Every upsert is committed together, so no completion can lack its job/outbox record.
    session.execute(
        insert(CourseCompletion).values(student_id=data.student_id, course_id=data.course_id)
        .on_conflict_do_nothing(index_elements=[CourseCompletion.student_id, CourseCompletion.course_id])
    )
    completion = session.scalar(
        select(CourseCompletion).where(CourseCompletion.student_id == data.student_id, CourseCompletion.course_id == data.course_id)
    )
    assert completion is not None
    candidate_job_id = str(uuid.uuid4())
    session.execute(
        insert(CertificateJob).values(id=candidate_job_id, completion_id=completion.id)
        .on_conflict_do_nothing(index_elements=[CertificateJob.completion_id])
    )
    job = session.scalar(select(CertificateJob).where(CertificateJob.completion_id == completion.id))
    assert job is not None
    session.execute(
        insert(OutboxEvent).values(id=str(uuid.uuid4()), certificate_job_id=job.id)
        .on_conflict_do_nothing(index_elements=[OutboxEvent.certificate_job_id])
    )
    session.commit()
    # A dispatch failure is recoverable because the outbox row remains unpublished.
    dispatch_outbox.delay()
    return JobResponse(job_id=job.id, state=job.state)


@app.get("/certificate-jobs/{job_id}", response_model=JobResponse)
def get_job(job_id: str, session: Session = Depends(get_session)) -> JobResponse:
    job = session.get(CertificateJob, job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Certificate job not found")
    return JobResponse(job_id=job.id, state=job.state)


def provider_headers(token: str, job_id: str) -> dict[str, str]:
    if not token:
        raise RuntimeError("External service token is not configured")
    return {"Authorization": f"Bearer {token}", "Idempotency-Key": job_id}


def claim_job(session: Session, job_id: str) -> tuple[CertificateJob, CourseCompletion, Student, Course] | None:
    job = session.scalar(select(CertificateJob).where(CertificateJob.id == job_id).with_for_update(skip_locked=True))
    if job is None or job.state == JobState.SENT:
        return None
    now = datetime.now(timezone.utc)
    if job.state == JobState.PROCESSING and job.locked_at and job.locked_at > now - LOCK_TTL:
        return None
    completion = session.get(CourseCompletion, job.completion_id)
    student = session.get(Student, completion.student_id) if completion else None
    course = session.get(Course, completion.course_id) if completion else None
    if not completion or not student or not course:
        job.state, job.last_error, job.locked_at = JobState.FAILED, "Required completion data is missing", None
        session.commit()
        return None
    job.state, job.locked_at, job.last_error = JobState.PROCESSING, now, None
    job.attempts += 1
    session.commit()  # Do not retain a PostgreSQL lock while calling external services.
    return job, completion, student, course


def request_certificate(job: CertificateJob, completion: CourseCompletion, student: Student, course: Course) -> str:
    if not CERTIFICATE_SERVICE_URL:
        raise RuntimeError("CERTIFICATE_SERVICE_URL is not configured")
    payload = {
        "certificate_id": job.id,
        "recipient_name": student.name,
        "recipient_email": student.email,
        "course_title": course.title,
        "completed_at": completion.completed_at.isoformat(),
    }
    response = httpx.post(CERTIFICATE_SERVICE_URL, json=payload, headers=provider_headers(CERTIFICATE_SERVICE_TOKEN, job.id), timeout=20)
    response.raise_for_status()
    certificate_url = response.json().get("certificate_url")
    if not isinstance(certificate_url, str):
        raise RuntimeError("Certificate service did not return certificate_url")
    return certificate_url


def request_email(job: CertificateJob, student: Student, course: Course, certificate_url: str) -> None:
    if not EMAIL_SERVICE_URL:
        raise RuntimeError("EMAIL_SERVICE_URL is not configured")
    payload = {
        "to": student.email,
        "template": "course-certificate",
        "variables": {"student_name": student.name, "course_title": course.title, "certificate_url": certificate_url},
    }
    response = httpx.post(EMAIL_SERVICE_URL, json=payload, headers=provider_headers(EMAIL_SERVICE_TOKEN, job.id), timeout=20)
    response.raise_for_status()


def record_failure(session: Session, job_id: str, error: Exception, terminal: bool) -> None:
    job = session.scalar(select(CertificateJob).where(CertificateJob.id == job_id).with_for_update())
    if job is not None and job.state != JobState.SENT:
        job.state = JobState.FAILED if terminal else JobState.PENDING
        job.locked_at, job.last_error = None, str(error)[:1000]
        session.commit()


@celery_app.task(bind=True, max_retries=5)
def process_certificate(self, job_id: str) -> None:
    with SessionLocal() as session:
        claimed = claim_job(session, job_id)
        if claimed is None:
            return
        job, completion, student, course = claimed
        try:
            certificate_url = job.certificate_url or request_certificate(job, completion, student, course)
            # Persist PDF progress before the second external side effect.
            current = session.scalar(select(CertificateJob).where(CertificateJob.id == job.id).with_for_update())
            if current is None:
                return
            current.certificate_url = certificate_url
            session.commit()
            request_email(job, student, course, certificate_url)
            current = session.scalar(select(CertificateJob).where(CertificateJob.id == job.id).with_for_update())
            if current is not None:
                current.state, current.locked_at = JobState.SENT, None
                current.sent_at = datetime.now(timezone.utc)
                session.commit()
                logger.info("certificate job sent operation_id=%s", job.id)
        except Exception as exc:
            session.rollback()
            terminal = self.request.retries >= self.max_retries
            record_failure(session, job_id, exc, terminal)
            logger.warning("certificate job failed operation_id=%s terminal=%s", job_id, terminal, exc_info=True)
            if not terminal:
                raise self.retry(exc=exc, countdown=min(300, 2 ** (self.request.retries + 1)))
            raise


@celery_app.task
def dispatch_outbox(batch_size: int = 100) -> int:
    """Publish pending outbox events; duplicate publication is harmless to the idempotent worker."""
    published = 0
    with SessionLocal() as session:
        for _ in range(batch_size):
            event = session.scalar(
                select(OutboxEvent).where(OutboxEvent.published_at.is_(None)).with_for_update(skip_locked=True).limit(1)
            )
            if event is None:
                break
            process_certificate.delay(event.certificate_job_id)
            event.published_at = datetime.now(timezone.utc)
            session.commit()
            logger.info("certificate job published operation_id=%s", event.certificate_job_id)
            published += 1
    return published
