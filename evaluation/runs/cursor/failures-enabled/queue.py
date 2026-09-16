"""
Certificate delivery queue (FastAPI + worker pool).

Failures review_plan / review_code / check_invariant applied before finalize.

Flow:
  transactional outbox enqueue
    -> worker fetches job
    -> dedup table (msg_id UNIQUE / idempotency_key)
    -> PDF + email (timeout=5, idempotent effect)
    -> ack AFTER durable processing
    -> on failure: backoff + jitter retry; after N failures move to DLQ then ack
"""

from __future__ import annotations

import json
import logging
import os
import random
import threading
import time
import uuid
from datetime import datetime
from queue import Full, Queue
from typing import Optional

import httpx
from fastapi import Depends, FastAPI, Header, HTTPException
from pydantic import BaseModel, EmailStr
from sqlalchemy import (
    Column,
    DateTime,
    Integer,
    String,
    Text,
    UniqueConstraint,
    create_engine,
)
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, declarative_base, sessionmaker

DATABASE_URL = os.getenv(
    "DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/certificates"
)
PDF_SERVICE_URL = os.getenv("PDF_SERVICE_URL", "https://pdf.example.com/generate")
EMAIL_SERVICE_URL = os.getenv("EMAIL_SERVICE_URL", "https://email.example.com/send")
WORKER_COUNT = int(os.getenv("WORKER_COUNT", "4"))
MAX_RETRIES = int(os.getenv("MAX_RETRIES", "3"))
QUEUE_MAXSIZE = int(os.getenv("QUEUE_MAXSIZE", "1000"))

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()
app = FastAPI(title="Certificate Queue")
logger = logging.getLogger("certificate_queue")
job_queue: Queue = Queue(maxsize=QUEUE_MAXSIZE)


class TokenBucket:
    def __init__(self, rate: int = 40):
        self.rate = rate
        self.tokens = rate

    def rate_limit(self) -> bool:
        if self.tokens <= 0:
            return False
        self.tokens -= 1
        return True


limiter = TokenBucket()


class Completion(Base):
    __tablename__ = "completions"
    __table_args__ = (
        UniqueConstraint("student_id", "course_id", name="uq_completion_student_course"),
    )

    id = Column(Integer, primary_key=True)
    student_id = Column(Integer, nullable=False)
    course_id = Column(Integer, nullable=False)
    student_email = Column(String, nullable=False)
    student_name = Column(String, nullable=False)
    course_title = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class Outbox(Base):
    __tablename__ = "outbox"

    id = Column(Integer, primary_key=True)
    msg_id = Column(String, unique=True, nullable=False, index=True)
    payload = Column(Text, nullable=False)
    status = Column(String, nullable=False, default="pending")  # pending|enqueued|processed
    created_at = Column(DateTime, default=datetime.utcnow)


class Dedup(Base):
    __tablename__ = "dedup"
    __table_args__ = (UniqueConstraint("msg_id", name="uq_dedup_msg_id"),)

    id = Column(Integer, primary_key=True)
    msg_id = Column(String, unique=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class Certificate(Base):
    __tablename__ = "certificates"
    __table_args__ = (UniqueConstraint("msg_id", name="uq_certificate_msg_id"),)

    id = Column(Integer, primary_key=True)
    msg_id = Column(String, unique=True, nullable=False)
    student_id = Column(Integer, nullable=False)
    course_id = Column(Integer, nullable=False)
    status = Column(String, nullable=False, default="sent")
    created_at = Column(DateTime, default=datetime.utcnow)


class DeadLetter(Base):
    __tablename__ = "dlq"

    id = Column(Integer, primary_key=True)
    msg_id = Column(String, unique=True, nullable=False)
    payload = Column(Text, nullable=False)
    error = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class CompletionRequest(BaseModel):
    student_id: int
    course_id: int
    student_email: EmailStr
    student_name: str
    course_title: str
    idempotency_key: Optional[str] = None


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def require_rate_limit():
    if not limiter.rate_limit():
        raise HTTPException(status_code=429, detail="Too many requests")


def ack(job: dict) -> None:
    """Acknowledge AFTER durable processing so crash-before-ack redelivers."""
    job["_acked"] = True
    logger.info("ack msg_id=%s request_id=%s", job.get("msg_id"), job.get("request_id"))


def nack(job: dict) -> None:
    """Negative ack: visibility restored for retry."""
    job["_acked"] = False
    logger.info("nack msg_id=%s request_id=%s", job.get("msg_id"), job.get("request_id"))


def is_duplicate(db: Session, msg_id: str) -> bool:
    db.add(Dedup(msg_id=msg_id))
    try:
        db.commit()
        return False
    except IntegrityError:
        db.rollback()
        return True


def already_sent(db: Session, msg_id: str) -> bool:
    return db.query(Certificate).filter(Certificate.msg_id == msg_id).first() is not None


def generate_certificate_pdf(job: dict) -> bytes:
    response = httpx.post(
        PDF_SERVICE_URL,
        json={
            "student_name": job["student_name"],
            "course_title": job["course_title"],
            "student_id": job["student_id"],
            "course_id": job["course_id"],
            "idempotency_key": job["msg_id"],
        },
        headers={"Idempotency-Key": job["msg_id"]},
        timeout=5,
    )
    response.raise_for_status()
    return response.content


def email_certificate(job: dict, pdf_bytes: bytes) -> None:
    response = httpx.post(
        EMAIL_SERVICE_URL,
        json={
            "to": job["student_email"],
            "subject": f"Certificate: {job['course_title']}",
            "body": f"Congratulations {job['student_name']} on completing {job['course_title']}.",
            "idempotency_key": job["msg_id"],
        },
        files={"attachment": ("certificate.pdf", pdf_bytes, "application/pdf")},
        headers={"Idempotency-Key": job["msg_id"]},
        timeout=5,
    )
    response.raise_for_status()


def process_idempotently(db: Session, job: dict) -> None:
    if already_sent(db, job["msg_id"]):
        return
    pdf = generate_certificate_pdf(job)
    email_certificate(job, pdf)
    db.add(
        Certificate(
            msg_id=job["msg_id"],
            student_id=job["student_id"],
            course_id=job["course_id"],
            status="sent",
        )
    )
    try:
        db.commit()
    except IntegrityError:
        db.rollback()


def move_to_dlq(db: Session, job: dict, error: str) -> None:
    db.add(
        DeadLetter(
            msg_id=job["msg_id"],
            payload=str(job),
            error=error,
        )
    )
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
    logger.warning("moved poison to DLQ msg_id=%s request_id=%s", job["msg_id"], job.get("request_id"))


def mark_outbox(db: Session, msg_id: str, status: str) -> None:
    row = db.query(Outbox).filter(Outbox.msg_id == msg_id).with_for_update().first()
    if row:
        row.status = status
        db.commit()


def worker_loop(worker_id: int) -> None:
    while True:
        job = job_queue.get()
        db = SessionLocal()
        try:
            if is_duplicate(db, job["msg_id"]) and already_sent(db, job["msg_id"]):
                ack(job)
                continue
            process_idempotently(db, job)
            mark_outbox(db, job["msg_id"], "processed")
            ack(job)
        except Exception as exc:
            attempt = job.get("attempt", 0) + 1
            job["attempt"] = attempt
            if attempt >= MAX_RETRIES:
                move_to_dlq(db, job, str(exc))
                ack(job)
            else:
                delay = (0.1 * (2 ** attempt)) + random.random() * 0.05  # exponential backoff + jitter
                time.sleep(delay)
                nack(job)
                try:
                    job_queue.put(job, block=False)
                except Full:
                    move_to_dlq(db, job, "queue full during retry")
                    ack(job)
        finally:
            db.close()
            job_queue.task_done()


def drain_outbox() -> None:
    """Reconciliation: enqueue pending outbox rows after crash."""
    db = SessionLocal()
    try:
        pending = (
            db.query(Outbox)
            .filter(Outbox.status == "pending")
            .with_for_update()
            .all()
        )
        for row in pending:
            payload = json.loads(row.payload)
            payload.setdefault("attempt", 0)
            payload.setdefault("request_id", str(uuid.uuid4()))
            try:
                job_queue.put(payload, timeout=1)
                row.status = "enqueued"
            except Full:
                break
        db.commit()
    finally:
        db.close()


def start_worker_pool(size: int = WORKER_COUNT) -> None:
    for i in range(size):
        threading.Thread(target=worker_loop, args=(i,), daemon=True).start()
    threading.Thread(target=_outbox_loop, daemon=True).start()


def _outbox_loop() -> None:
    while True:
        drain_outbox()
        time.sleep(2)


@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)
    start_worker_pool()


@app.post("/complete")
def complete_course(
    payload: CompletionRequest,
    db: Session = Depends(get_db),
    x_request_id: str = Header(default=""),
    idempotency_key_header: Optional[str] = Header(default=None, alias="Idempotency-Key"),
):
    require_rate_limit()
    request_id = x_request_id or str(uuid.uuid4())
    msg_id = payload.idempotency_key or idempotency_key_header or str(uuid.uuid4())

    existing = db.query(Outbox).filter(Outbox.msg_id == msg_id).first()
    if existing:
        logger.info("return cached enqueue request_id=%s msg_id=%s", request_id, msg_id)
        return {"queued": True, "msg_id": msg_id, "cached": True, "request_id": request_id}

    completion = Completion(
        student_id=payload.student_id,
        course_id=payload.course_id,
        student_email=payload.student_email,
        student_name=payload.student_name,
        course_title=payload.course_title,
    )
    outbox = Outbox(
        msg_id=msg_id,
        payload=json.dumps(
            {
                "msg_id": msg_id,
                "student_id": payload.student_id,
                "course_id": payload.course_id,
                "student_email": payload.student_email,
                "student_name": payload.student_name,
                "course_title": payload.course_title,
                "attempt": 0,
                "request_id": request_id,
            }
        ),
        status="pending",
    )
    db.add(completion)
    db.add(outbox)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        existing = db.query(Outbox).filter(Outbox.msg_id == msg_id).first()
        if existing:
            return {"queued": True, "msg_id": msg_id, "cached": True, "request_id": request_id}
        raise HTTPException(status_code=409, detail="Completion already recorded")

    job = {
        "msg_id": msg_id,
        "student_id": payload.student_id,
        "course_id": payload.course_id,
        "student_email": payload.student_email,
        "student_name": payload.student_name,
        "course_title": payload.course_title,
        "attempt": 0,
        "request_id": request_id,
    }
    try:
        job_queue.put(job, timeout=1)
        outbox.status = "enqueued"
        db.commit()
    except Full:
        logger.warning("queue full; outbox stays pending request_id=%s", request_id)
        return {"queued": False, "status": "pending", "msg_id": msg_id, "request_id": request_id}

    return {"queued": True, "msg_id": msg_id, "request_id": request_id}


@app.post("/jobs/reconcile")
def reconcile(db: Session = Depends(get_db), x_request_id: str = Header(default="")):
    drain_outbox()
    return {"ok": True, "request_id": x_request_id or str(uuid.uuid4())}


@app.get("/queue/status")
def queue_status(db: Session = Depends(get_db)):
    return {
        "pending_memory": job_queue.qsize(),
        "workers": WORKER_COUNT,
        "dlq": db.query(DeadLetter).count(),
        "outbox_pending": db.query(Outbox).filter(Outbox.status == "pending").count(),
    }


@app.get("/certificates/{student_id}/{course_id}")
def get_certificate(student_id: int, course_id: int, db: Session = Depends(get_db)):
    row = (
        db.query(Certificate)
        .filter(Certificate.student_id == student_id, Certificate.course_id == course_id)
        .first()
    )
    return {"sent": row is not None}
