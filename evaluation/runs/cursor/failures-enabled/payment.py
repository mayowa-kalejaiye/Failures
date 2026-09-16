"""
Course payment and enrollment (FastAPI + PostgreSQL + Paystack).

Failures review_plan / review_code / check_invariant were applied before finalize.

State machine:
  pending (durable, idempotency_key UNIQUE)
    -> Paystack (timeout=5, Idempotency-Key)
    -> success | failure | ambiguous (timeout)
    -> reconciliation (poll Paystack or webhook event_id UNIQUE)
    -> verified payment
    -> enrollment (idempotent, gated on verified, SELECT FOR UPDATE)
"""

from __future__ import annotations

import logging
import os
import uuid
from datetime import datetime
from typing import Optional

import httpx
from fastapi import Depends, FastAPI, Header, HTTPException, Request
from pydantic import BaseModel, EmailStr
from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
    create_engine,
    text,
)
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, declarative_base, sessionmaker

DATABASE_URL = os.getenv(
    "DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/courses"
)
PAYSTACK_SECRET_KEY = os.getenv("PAYSTACK_SECRET_KEY", "sk_test_replace_me")
PAYSTACK_BASE_URL = os.getenv("PAYSTACK_BASE_URL", "https://api.paystack.co")
PAYSTACK_CALLBACK_URL = os.getenv(
    "PAYSTACK_CALLBACK_URL", "http://localhost:8000/payments/callback"
)

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()
app = FastAPI(title="Course Payments")
logger = logging.getLogger("payments")


class TokenBucket:
    """Simple rate limiter for mutating endpoints."""

    def __init__(self, rate: int = 30):
        self.rate = rate
        self.tokens = rate

    def rate_limit(self) -> bool:
        if self.tokens <= 0:
            return False
        self.tokens -= 1
        return True


limiter = TokenBucket()


class Student(Base):
    __tablename__ = "students"
    id = Column(Integer, primary_key=True)
    email = Column(String, unique=True, nullable=False)
    full_name = Column(String, nullable=False)


class Course(Base):
    __tablename__ = "courses"
    id = Column(Integer, primary_key=True)
    title = Column(String, nullable=False)
    price_kobo = Column(Integer, nullable=False)


class Payment(Base):
    __tablename__ = "payments"
    __table_args__ = (UniqueConstraint("idempotency_key", name="uq_payments_idempotency_key"),)

    id = Column(Integer, primary_key=True)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False)
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=False)
    amount_kobo = Column(Integer, nullable=False)
    reference = Column(String, unique=True, nullable=False)
    idempotency_key = Column(String, unique=True, nullable=False, index=True)
    status = Column(String, nullable=False, default="pending")  # pending|completed|failed
    paystack_access_code = Column(String, nullable=True)
    cached_response = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    paid_at = Column(DateTime, nullable=True)


class Enrollment(Base):
    __tablename__ = "enrollments"
    __table_args__ = (UniqueConstraint("student_id", "course_id", name="uq_enrollment_student_course"),)

    id = Column(Integer, primary_key=True)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False)
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=False)
    payment_id = Column(Integer, ForeignKey("payments.id"), nullable=False)
    granted_at = Column(DateTime, default=datetime.utcnow)


class WebhookEvent(Base):
    __tablename__ = "webhook_events"
    __table_args__ = (UniqueConstraint("event_id", name="uq_webhook_event_id"),)

    id = Column(Integer, primary_key=True)
    event_id = Column(String, unique=True, nullable=False)
    processed_at = Column(DateTime, default=datetime.utcnow)


class StudentCreate(BaseModel):
    email: EmailStr
    full_name: str


class CourseCreate(BaseModel):
    title: str
    price_kobo: int


class InitializePaymentRequest(BaseModel):
    student_id: int
    course_id: int
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


def paystack_headers(idempotency_key: str) -> dict:
    return {
        "Authorization": f"Bearer {PAYSTACK_SECRET_KEY}",
        "Content-Type": "application/json",
        "Idempotency-Key": idempotency_key,
    }


def insert_pending_payment(
    db: Session,
    student_id: int,
    course_id: int,
    amount_kobo: int,
    idempotency_key: str,
    request_id: str,
) -> Payment:
    """Durable pending row BEFORE any provider call. Unique on idempotency_key."""
    existing = (
        db.query(Payment)
        .filter(Payment.idempotency_key == idempotency_key)
        .with_for_update()
        .first()
    )
    if existing:
        return existing

    payment = Payment(
        student_id=student_id,
        course_id=course_id,
        amount_kobo=amount_kobo,
        reference=f"crs_{uuid.uuid4().hex}",
        idempotency_key=idempotency_key,
        status="pending",
        cached_response=None,
    )
    db.add(payment)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        existing = (
            db.query(Payment)
            .filter(Payment.idempotency_key == idempotency_key)
            .first()
        )
        if existing:
            logger.info("duplicate idempotency_key request_id=%s", request_id)
            return existing
        raise
    db.refresh(payment)
    logger.info("pending payment persisted request_id=%s payment_id=%s", request_id, payment.id)
    return payment


def initialize_paystack(email: str, amount_kobo: int, reference: str, idempotency_key: str) -> dict:
    payload = {
        "email": email,
        "amount": amount_kobo,
        "reference": reference,
        "callback_url": PAYSTACK_CALLBACK_URL,
        "currency": "NGN",
    }
    response = httpx.post(
        f"{PAYSTACK_BASE_URL}/transaction/initialize",
        json=payload,
        headers=paystack_headers(idempotency_key),
        timeout=5,
    )
    body = response.json()
    if response.status_code != 200 or not body.get("status"):
        raise HTTPException(status_code=502, detail=body.get("message", "Paystack error"))
    return body["data"]


def verify_paystack(reference: str, idempotency_key: str) -> dict:
    response = httpx.get(
        f"{PAYSTACK_BASE_URL}/transaction/verify/{reference}",
        headers=paystack_headers(idempotency_key),
        timeout=5,
    )
    body = response.json()
    if response.status_code != 200 or not body.get("status"):
        raise HTTPException(status_code=502, detail=body.get("message", "Verify failed"))
    return body["data"]


def enroll_if_verified(db: Session, payment: Payment, request_id: str) -> Optional[Enrollment]:
    """Enrollment is gated on verified completed payment and is idempotent."""
    locked = (
        db.query(Payment)
        .filter(Payment.id == payment.id)
        .with_for_update()
        .first()
    )
    if not locked or locked.status != "completed":
        logger.info("skip enrollment; payment not verified request_id=%s", request_id)
        return None

    existing = (
        db.query(Enrollment)
        .filter(
            Enrollment.student_id == locked.student_id,
            Enrollment.course_id == locked.course_id,
        )
        .with_for_update()
        .first()
    )
    if existing:
        return existing

    enrollment = Enrollment(
        student_id=locked.student_id,
        course_id=locked.course_id,
        payment_id=locked.id,
    )
    db.add(enrollment)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        return (
            db.query(Enrollment)
            .filter(
                Enrollment.student_id == locked.student_id,
                Enrollment.course_id == locked.course_id,
            )
            .first()
        )
    db.refresh(enrollment)
    logger.info("enrollment granted request_id=%s enrollment_id=%s", request_id, enrollment.id)
    return enrollment


def mark_completed_and_enroll(db: Session, payment: Payment, request_id: str) -> Enrollment:
    db.execute(
        text(
            "SELECT id FROM payments WHERE id = :id FOR UPDATE"
        ),
        {"id": payment.id},
    )
    payment.status = "completed"
    payment.paid_at = datetime.utcnow()
    db.commit()
    enrollment = enroll_if_verified(db, payment, request_id)
    if enrollment is None:
        raise HTTPException(status_code=409, detail="Enrollment refused: payment not verified")
    return enrollment


@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)


@app.post("/students", status_code=201)
def create_student(
    payload: StudentCreate,
    db: Session = Depends(get_db),
    x_request_id: str = Header(default=""),
):
    require_rate_limit()
    request_id = x_request_id or str(uuid.uuid4())
    student = Student(email=payload.email, full_name=payload.full_name)
    db.add(student)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Student already exists")
    db.refresh(student)
    logger.info("student created request_id=%s student_id=%s", request_id, student.id)
    return {"id": student.id, "email": student.email, "request_id": request_id}


@app.post("/courses", status_code=201)
def create_course(payload: CourseCreate, db: Session = Depends(get_db)):
    require_rate_limit()
    course = Course(title=payload.title, price_kobo=payload.price_kobo)
    db.add(course)
    db.commit()
    db.refresh(course)
    return {"id": course.id, "title": course.title, "price_kobo": course.price_kobo}


@app.get("/courses")
def list_courses(db: Session = Depends(get_db)):
    courses = db.query(Course).all()
    return [{"id": c.id, "title": c.title, "price_kobo": c.price_kobo} for c in courses]


@app.post("/payments/initialize")
def initialize_payment(
    payload: InitializePaymentRequest,
    db: Session = Depends(get_db),
    x_request_id: str = Header(default=""),
    idempotency_key_header: Optional[str] = Header(default=None, alias="Idempotency-Key"),
):
    require_rate_limit()
    request_id = x_request_id or str(uuid.uuid4())
    student = db.query(Student).filter(Student.id == payload.student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    course = db.query(Course).filter(Course.id == payload.course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    idempotency_key = payload.idempotency_key or idempotency_key_header or str(uuid.uuid4())

    # 1) persist pending locally (unique idempotency_key) before Paystack
    payment = insert_pending_payment(
        db, student.id, course.id, course.price_kobo, idempotency_key, request_id
    )

    if payment.status == "completed" and payment.cached_response:
        logger.info("return cached response request_id=%s", request_id)
        return {
            "status": "completed",
            "reference": payment.reference,
            "cached": True,
            "request_id": request_id,
            "authorization_url": payment.cached_response,
        }

    if payment.paystack_access_code and payment.cached_response:
        return {
            "status": payment.status,
            "reference": payment.reference,
            "authorization_url": payment.cached_response,
            "access_code": payment.paystack_access_code,
            "request_id": request_id,
            "cached": True,
        }

    # 2) provider call; timeout is ambiguous, not failure
    try:
        data = initialize_paystack(
            student.email, course.price_kobo, payment.reference, idempotency_key
        )
    except httpx.TimeoutException:
        logger.warning("Paystack timeout; leave pending for reconciliation request_id=%s", request_id)
        return {
            "status": "pending",
            "message": "Provider timeout, reconciling",
            "reference": payment.reference,
            "request_id": request_id,
        }
    except HTTPException:
        payment.status = "failed"
        db.commit()
            raise

    payment.paystack_access_code = data.get("access_code")
    payment.cached_response = data.get("authorization_url")
    db.commit()

    return {
        "status": "pending",
        "authorization_url": data["authorization_url"],
        "access_code": data["access_code"],
        "reference": payment.reference,
        "idempotency_key": idempotency_key,
        "request_id": request_id,
    }


@app.get("/payments/callback")
def payment_callback(reference: str, db: Session = Depends(get_db), x_request_id: str = Header(default="")):
    request_id = x_request_id or str(uuid.uuid4())
    payment = db.query(Payment).filter(Payment.reference == reference).first()
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")
    data = verify_paystack(reference, payment.idempotency_key)
    if data.get("status") == "success":
        enrollment = mark_completed_and_enroll(db, payment, request_id)
        return {
            "status": "completed",
            "enrollment_id": enrollment.id,
            "request_id": request_id,
        }
    if data.get("status") in {"failed", "abandoned"}:
        payment.status = "failed"
        db.commit()
    return {"status": payment.status, "request_id": request_id}


@app.post("/webhooks/paystack")
async def paystack_webhook(request: Request, db: Session = Depends(get_db)):
    body = await request.json()
    request_id = request.headers.get("x-request-id") or str(uuid.uuid4())
    event_id = str(body.get("id") or body.get("event_id") or body.get("data", {}).get("id") or "")
    if not event_id:
        raise HTTPException(status_code=400, detail="Missing event_id")

    # webhook dedup via event_id UNIQUE
    db.add(WebhookEvent(event_id=event_id))
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        return {"status": "already_processed", "event_id": event_id, "request_id": request_id}

    data = body.get("data") or {}
    reference = data.get("reference")
    payment = db.query(Payment).filter(Payment.reference == reference).first()
    if not payment:
        return {"status": "ignored", "reason": "unknown reference", "request_id": request_id}

    if body.get("event") == "charge.success" or data.get("status") == "success":
        mark_completed_and_enroll(db, payment, request_id)

    return {"status": "ok", "event_id": event_id, "request_id": request_id}


def reconcile_pending_payments(db: Session, request_id: str = "") -> dict:
    """Poll Paystack for pending rows after timeout/crash; then enroll if verified."""
    request_id = request_id or str(uuid.uuid4())
    pending = db.query(Payment).filter(Payment.status == "pending").all()
    completed = 0
    for payment in pending:
        try:
            data = verify_paystack(payment.reference, payment.idempotency_key)
        except (httpx.TimeoutException, HTTPException):
            continue
        if data.get("status") == "success":
            mark_completed_and_enroll(db, payment, request_id)
            completed += 1
        elif data.get("status") in {"failed", "abandoned"}:
            payment.status = "failed"
            db.commit()
    logger.info("reconciliation finished request_id=%s completed=%s", request_id, completed)
    return {"reconciled": completed, "request_id": request_id}


@app.post("/jobs/reconcile")
def reconcile_job(db: Session = Depends(get_db), x_request_id: str = Header(default="")):
    return reconcile_pending_payments(db, x_request_id or str(uuid.uuid4()))


@app.get("/enrollments/{student_id}")
def list_enrollments(student_id: int, db: Session = Depends(get_db)):
    rows = db.query(Enrollment).filter(Enrollment.student_id == student_id).all()
    return [{"enrollment_id": r.id, "course_id": r.course_id, "payment_id": r.payment_id} for r in rows]


@app.get("/access/{student_id}/{course_id}")
def check_access(student_id: int, course_id: int, db: Session = Depends(get_db)):
    enrollment = (
        db.query(Enrollment)
        .filter(Enrollment.student_id == student_id, Enrollment.course_id == course_id)
        .first()
    )
    return {"has_access": enrollment is not None}
