"""Course-completion certificate jobs using FastAPI, PostgreSQL, Celery, and Redis.

Run the API with ``uvicorn queue:app`` and workers with:
``celery -A queue.celery_app worker --loglevel=INFO --concurrency=4``.

Required settings: DATABASE_URL, REDIS_URL, CERTIFICATE_SERVICE_URL,
CERTIFICATE_SERVICE_TOKEN, EMAIL_SERVICE_URL, and EMAIL_SERVICE_TOKEN.
"""

from __future__ import annotations

import os
import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Generator

import httpx
from celery import Celery
from fastapi import Depends, FastAPI, HTTPException, status
from pydantic import BaseModel, EmailStr
from sqlalchemy import DateTime, ForeignKey, Integer, String, UniqueConstraint, create_engine, select
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, sessionmaker


DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql+psycopg://postgres:postgres@localhost/courses")
REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
CERTIFICATE_SERVICE_URL = os.environ.get("CERTIFICATE_SERVICE_URL", "")
CERTIFICATE_SERVICE_TOKEN = os.environ.get("CERTIFICATE_SERVICE_TOKEN", "")
EMAIL_SERVICE_URL = os.environ.get("EMAIL_SERVICE_URL", "")
EMAIL_SERVICE_TOKEN = os.environ.get("EMAIL_SERVICE_TOKEN", "")


class Base(DeclarativeBase):
    pass


class JobStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    SENT = "sent"
    FAILED = "failed"


class Student(Base):
    __tablename__ = "students"
    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(320), unique=True)
    name: Mapped[str] = mapped_column(String(200))


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
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    completion_id: Mapped[int] = mapped_column(ForeignKey("course_completions.id"), index=True)
    state: Mapped[JobStatus] = mapped_column(default=JobStatus.PENDING, index=True)
    attempts: Mapped[int] = mapped_column(Integer, default=0)
    certificate_url: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    last_error: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(engine, expire_on_commit=False)
celery_app = Celery("certificate_jobs", broker=REDIS_URL, backend=REDIS_URL)
celery_app.conf.update(task_acks_late=True, task_reject_on_worker_lost=True, worker_prefetch_multiplier=1)
app = FastAPI(title="Certificate jobs")


class CompletionRequest(BaseModel):
    student_id: int
    course_id: int


class JobResponse(BaseModel):
    job_id: str
    state: JobStatus


def get_session() -> Generator[Session, None, None]:
    with SessionLocal() as session:
        yield session


def enqueue_once(session: Session, completion_id: int) -> CertificateJob:
    """Create at most one job for a completion; its database key is the dedupe key."""
    job = session.scalar(select(CertificateJob).where(CertificateJob.completion_id == completion_id))
    if job is None:
        job = CertificateJob(completion_id=completion_id)
        session.add(job)
        session.flush()
    return job


@app.on_event("startup")
def create_tables() -> None:
    Base.metadata.create_all(engine)


@app.post("/completions", response_model=JobResponse, status_code=status.HTTP_202_ACCEPTED)
def record_completion(data: CompletionRequest, session: Session = Depends(get_session)) -> JobResponse:
    student = session.get(Student, data.student_id)
    course = session.get(Course, data.course_id)
    if student is None or course is None:
        raise HTTPException(status_code=404, detail="Student or course not found")

    completion = session.scalar(
        select(CourseCompletion).where(CourseCompletion.student_id == data.student_id, CourseCompletion.course_id == data.course_id)
    )
    if completion is None:
        completion = CourseCompletion(student_id=data.student_id, course_id=data.course_id)
        session.add(completion)
        session.flush()
    job = enqueue_once(session, completion.id)
    session.commit()  # A worker never sees a job until both completion and job are durable.

    # Delivery may be duplicated if this process crashes after commit. The worker is idempotent.
    send_certificate.delay(job.id)
    return JobResponse(job_id=job.id, state=job.state)


@app.get("/certificate-jobs/{job_id}", response_model=JobResponse)
def certificate_job(job_id: str, session: Session = Depends(get_session)) -> JobResponse:
    job = session.get(CertificateJob, job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Certificate job not found")
    return JobResponse(job_id=job.id, state=job.state)


def service_headers(token: str, job_id: str) -> dict[str, str]:
    if not token:
        raise RuntimeError("External service token is not configured")
    return {"Authorization": f"Bearer {token}", "Idempotency-Key": job_id}


def claim_job(session: Session, job_id: str) -> tuple[CertificateJob, CourseCompletion, Student, Course] | None:
    """Claim a job in a short transaction; never hold a database lock over HTTP."""
    job = session.scalar(select(CertificateJob).where(CertificateJob.id == job_id).with_for_update(skip_locked=True))
    if job is None or job.state == JobStatus.SENT:
        return None
    completion = session.get(CourseCompletion, job.completion_id)
    if completion is None:
        job.state, job.last_error = JobStatus.FAILED, "Completion no longer exists"
        session.commit()
        return None
    student, course = session.get(Student, completion.student_id), session.get(Course, completion.course_id)
    if student is None or course is None:
        job.state, job.last_error = JobStatus.FAILED, "Student or course no longer exists"
        session.commit()
        return None
    job.state = JobStatus.PROCESSING
    job.attempts += 1
    job.last_error = None
    session.commit()
    return job, completion, student, course


def generate_certificate(job: CertificateJob, completion: CourseCompletion, student: Student, course: Course) -> str:
    if not CERTIFICATE_SERVICE_URL:
        raise RuntimeError("CERTIFICATE_SERVICE_URL is not configured")
    payload = {
        "recipient_name": student.name,
        "recipient_email": student.email,
        "course_title": course.title,
        "completed_at": completion.completed_at.isoformat(),
        "certificate_id": job.id,
    }
    response = httpx.post(CERTIFICATE_SERVICE_URL, json=payload, headers=service_headers(CERTIFICATE_SERVICE_TOKEN, job.id), timeout=20)
    response.raise_for_status()
    url = response.json().get("certificate_url")
    if not isinstance(url, str):
        raise RuntimeError("Certificate service response did not include certificate_url")
    return url


def send_email(job: CertificateJob, student: Student, course: Course, certificate_url: str) -> None:
    if not EMAIL_SERVICE_URL:
        raise RuntimeError("EMAIL_SERVICE_URL is not configured")
    payload = {
        "to": student.email,
        "template": "course-certificate",
        "variables": {"student_name": student.name, "course_title": course.title, "certificate_url": certificate_url},
    }
    response = httpx.post(EMAIL_SERVICE_URL, json=payload, headers=service_headers(EMAIL_SERVICE_TOKEN, job.id), timeout=20)
    response.raise_for_status()


@celery_app.task(bind=True, autoretry_for=(httpx.HTTPError,), retry_backoff=True, retry_jitter=True, max_retries=5)
def send_certificate(self, job_id: str) -> None:
    with SessionLocal() as session:
        claimed = claim_job(session, job_id)
        if claimed is None:
            return
        job, completion, student, course = claimed
        try:
            # Both providers receive the same durable key: retries reuse their prior result.
            certificate_url = job.certificate_url or generate_certificate(job, completion, student, course)
            send_email(job, student, course, certificate_url)
            current = session.scalar(select(CertificateJob).where(CertificateJob.id == job.id).with_for_update())
            if current is not None:
                current.certificate_url = certificate_url
                current.state = JobStatus.SENT
                current.sent_at = datetime.now(timezone.utc)
                session.commit()
        except Exception as exc:
            session.rollback()
            current = session.scalar(select(CertificateJob).where(CertificateJob.id == job.id).with_for_update())
            if current is not None:
                current.state = JobStatus.FAILED if self.request.retries >= self.max_retries else JobStatus.PENDING
                current.last_error = str(exc)[:1000]
                session.commit()
            raise
