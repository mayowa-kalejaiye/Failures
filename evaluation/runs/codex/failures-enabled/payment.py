"""Idempotent FastAPI course checkout and enrollment with PostgreSQL and Paystack.

Required environment variables: DATABASE_URL (using postgresql+asyncpg) and
PAYSTACK_SECRET_KEY. Amounts are persisted as integer minor units, never floats.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import os
import asyncio
import time
import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Any

import httpx
from fastapi import Depends, FastAPI, Header, HTTPException, Request, status
from pydantic import BaseModel, EmailStr, HttpUrl
from sqlalchemy import DateTime, ForeignKey, Integer, String, UniqueConstraint, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://postgres:postgres@localhost/courses")
PAYSTACK_SECRET_KEY = os.getenv("PAYSTACK_SECRET_KEY", "")
PAYSTACK_BASE_URL = "https://api.paystack.co"


class Base(DeclarativeBase):
    pass


class PaymentStatus(str, Enum):
    PENDING = "pending"
    SUCCEEDED = "succeeded"
    FAILED = "failed"


class Student(Base):
    __tablename__ = "students"
    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(320), unique=True, index=True)


class Course(Base):
    __tablename__ = "courses"
    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(200))
    price_minor: Mapped[int] = mapped_column(Integer)
    currency: Mapped[str] = mapped_column(String(3), default="NGN")
    is_published: Mapped[bool] = mapped_column(default=True)


class Payment(Base):
    __tablename__ = "payments"
    __table_args__ = (UniqueConstraint("idempotency_key", name="uq_payment_idempotency_key"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    reference: Mapped[str] = mapped_column(String(80), unique=True, index=True)
    idempotency_key: Mapped[str] = mapped_column(String(255))
    student_id: Mapped[int] = mapped_column(ForeignKey("students.id"), index=True)
    course_id: Mapped[int] = mapped_column(ForeignKey("courses.id"), index=True)
    amount_minor: Mapped[int] = mapped_column(Integer)
    currency: Mapped[str] = mapped_column(String(3))
    status: Mapped[PaymentStatus] = mapped_column(default=PaymentStatus.PENDING)
    authorization_url: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    paystack_transaction_id: Mapped[str | None] = mapped_column(String(80), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    paid_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class Enrollment(Base):
    __tablename__ = "enrollments"
    __table_args__ = (UniqueConstraint("student_id", "course_id", name="uq_enrollment_student_course"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("students.id"), index=True)
    course_id: Mapped[int] = mapped_column(ForeignKey("courses.id"), index=True)
    payment_id: Mapped[int] = mapped_column(ForeignKey("payments.id"), unique=True)
    enrolled_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


class WebhookEvent(Base):
    __tablename__ = "webhook_events"
    event_key: Mapped[str] = mapped_column(String(120), primary_key=True)
    received_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


engine: AsyncEngine | None = None
SessionLocal: async_sessionmaker[AsyncSession] | None = None
app = FastAPI(title="Course payments")


class TokenBucket:
    """Small admission-control guard; use a shared gateway limiter when scaled out."""

    def __init__(self, capacity: int = 30, refill_per_second: float = 0.5) -> None:
        self.capacity = capacity
        self.refill_per_second = refill_per_second
        self.buckets: dict[str, tuple[float, float]] = {}
        self.lock = asyncio.Lock()

    async def consume(self, key: str) -> bool:
        async with self.lock:
            now = time.monotonic()
            tokens, updated = self.buckets.get(key, (float(self.capacity), now))
            tokens = min(self.capacity, tokens + (now - updated) * self.refill_per_second)
            if tokens < 1:
                self.buckets[key] = (tokens, now)
                return False
            self.buckets[key] = (tokens - 1, now)
            return True


mutating_limiter = TokenBucket()


async def rate_limit(request: Request) -> None:
    client = request.client.host if request.client else "unknown"
    if not await mutating_limiter.consume(client):
        raise HTTPException(status_code=429, detail="Too many requests")


class CheckoutRequest(BaseModel):
    email: EmailStr
    course_id: int
    callback_url: HttpUrl | None = None


class CheckoutResponse(BaseModel):
    reference: str
    authorization_url: str


async def get_session() -> AsyncSession:
    if SessionLocal is None:
        raise HTTPException(status_code=503, detail="Database is not initialized")
    async with SessionLocal() as session:
        yield session


def paystack_headers() -> dict[str, str]:
    if not PAYSTACK_SECRET_KEY:
        raise HTTPException(status_code=500, detail="PAYSTACK_SECRET_KEY is not configured")
    return {"Authorization": f"Bearer {PAYSTACK_SECRET_KEY}"}


async def initialize_paystack(payment: Payment, student: Student, callback_url: HttpUrl | None) -> str:
    body: dict[str, Any] = {
        "email": student.email,
        "amount": payment.amount_minor,
        "currency": payment.currency,
        "reference": payment.reference,
    }
    if callback_url:
        body["callback_url"] = str(callback_url)
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            response = await client.post(f"{PAYSTACK_BASE_URL}/transaction/initialize", headers=paystack_headers(), json=body)
            response.raise_for_status()
            payload = response.json()
            url = payload.get("data", {}).get("authorization_url") if payload.get("status") else None
    except (httpx.HTTPError, ValueError) as exc:
        raise HTTPException(status_code=502, detail="Could not initialize payment") from exc
    if not isinstance(url, str):
        raise HTTPException(status_code=502, detail="Paystack rejected payment initialization")
    return url


async def verify_paystack(reference: str) -> dict[str, Any]:
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            response = await client.get(f"{PAYSTACK_BASE_URL}/transaction/verify/{reference}", headers=paystack_headers())
            response.raise_for_status()
            payload = response.json()
    except (httpx.HTTPError, ValueError) as exc:
        raise HTTPException(status_code=502, detail="Could not verify payment") from exc
    transaction = payload.get("data") if payload.get("status") else None
    if not isinstance(transaction, dict):
        raise HTTPException(status_code=502, detail="Invalid verification response from Paystack")
    return transaction


async def fulfill_payment(session: AsyncSession, reference: str) -> Payment:
    """Only a Paystack-verified transaction can create an enrollment."""
    transaction = await verify_paystack(reference)
    payment = await session.scalar(select(Payment).where(Payment.reference == reference).with_for_update())
    if payment is None:
        raise HTTPException(status_code=404, detail="Unknown payment reference")
    student = await session.scalar(select(Student).where(Student.id == payment.student_id).with_for_update())
    transaction_email = str(transaction.get("customer", {}).get("email", "")).lower()
    valid = (
        student is not None
        and transaction.get("status") == "success"
        and transaction.get("reference") == payment.reference
        and transaction.get("amount") == payment.amount_minor
        and transaction.get("currency") == payment.currency
        and transaction_email == student.email.lower()
    )
    if not valid:
        if transaction.get("status") in {"failed", "abandoned", "reversed"}:
            payment.status = PaymentStatus.FAILED
            await session.commit()
        raise HTTPException(status_code=400, detail="Payment has not been successfully verified")

    if payment.status != PaymentStatus.SUCCEEDED:
        payment.status = PaymentStatus.SUCCEEDED
        payment.paystack_transaction_id = str(transaction["id"])
        payment.paid_at = datetime.now(timezone.utc)
    existing = await session.scalar(
        select(Enrollment).where(Enrollment.student_id == payment.student_id, Enrollment.course_id == payment.course_id)
    )
    if existing is None:
        session.add(Enrollment(student_id=payment.student_id, course_id=payment.course_id, payment_id=payment.id))
    await session.commit()
    await session.refresh(payment)
    return payment


@app.on_event("startup")
async def start_database() -> None:
    global engine, SessionLocal
    engine = create_async_engine(DATABASE_URL, pool_pre_ping=True)
    SessionLocal = async_sessionmaker(engine, expire_on_commit=False)
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)


@app.post("/checkout", response_model=CheckoutResponse, status_code=status.HTTP_201_CREATED)
async def checkout(
    data: CheckoutRequest,
    request: Request,
    idempotency_key: str = Header(alias="Idempotency-Key", min_length=8, max_length=255),
    session: AsyncSession = Depends(get_session),
) -> CheckoutResponse:
    await rate_limit(request)
    course = await session.get(Course, data.course_id)
    if course is None or not course.is_published or course.price_minor <= 0:
        raise HTTPException(status_code=404, detail="Course not available")
    email = data.email.lower()
    # PostgreSQL upserts make concurrent first attempts converge on one payment row.
    await session.execute(insert(Student).values(email=email).on_conflict_do_nothing(index_elements=[Student.email]))
    student = await session.scalar(select(Student).where(Student.email == email))
    assert student is not None
    await session.execute(
        insert(Payment).values(
            reference=f"course_{uuid.uuid4().hex}", idempotency_key=idempotency_key,
            student_id=student.id, course_id=course.id, amount_minor=course.price_minor, currency=course.currency,
        ).on_conflict_do_nothing(index_elements=[Payment.idempotency_key])
    )
    await session.commit()  # Durable recovery point before the retryable provider call.

    # The row lock prevents simultaneous retries from producing two initializations.
    payment = await session.scalar(select(Payment).where(Payment.idempotency_key == idempotency_key).with_for_update())
    assert payment is not None
    payment_student = await session.get(Student, payment.student_id)
    if payment.course_id != course.id or payment_student is None or payment_student.email != email:
        raise HTTPException(status_code=409, detail="Idempotency key belongs to a different checkout")
    if payment.authorization_url:
        return CheckoutResponse(reference=payment.reference, authorization_url=payment.authorization_url)
    if payment.status == PaymentStatus.SUCCEEDED:
        raise HTTPException(status_code=409, detail="This checkout is already paid")
    authorization_url = await initialize_paystack(payment, payment_student, data.callback_url)
    payment.authorization_url = authorization_url
    await session.commit()
    return CheckoutResponse(reference=payment.reference, authorization_url=authorization_url)


@app.get("/payments/{reference}/verify")
async def verify_payment(reference: str, session: AsyncSession = Depends(get_session)) -> dict[str, str]:
    payment = await fulfill_payment(session, reference)
    return {"reference": payment.reference, "status": payment.status.value, "message": "Enrollment active"}


@app.post("/paystack/webhook")
async def paystack_webhook(
    request: Request,
    x_paystack_signature: str | None = Header(default=None),
    session: AsyncSession = Depends(get_session),
) -> dict[str, bool]:
    await rate_limit(request)
    raw_body = await request.body()
    expected = hmac.new(PAYSTACK_SECRET_KEY.encode(), raw_body, hashlib.sha512).hexdigest()
    if not PAYSTACK_SECRET_KEY or not x_paystack_signature or not hmac.compare_digest(expected, x_paystack_signature):
        raise HTTPException(status_code=401, detail="Invalid Paystack signature")
    try:
        event = json.loads(raw_body)
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=400, detail="Invalid webhook JSON") from exc
    if event.get("event") != "charge.success":
        return {"received": True}
    data = event.get("data", {})
    reference, transaction_id = data.get("reference"), data.get("id")
    if not isinstance(reference, str) or transaction_id is None:
        raise HTTPException(status_code=400, detail="Webhook lacks transaction identity")
    event_key = f"charge.success:{transaction_id}"
    inserted = await session.execute(insert(WebhookEvent).values(event_key=event_key).on_conflict_do_nothing())
    if inserted.rowcount == 0:
        return {"received": True}  # Previously committed alongside its fulfillment.
    try:
        await fulfill_payment(session, reference)
    except Exception:
        await session.rollback()  # Do not retain the dedup marker after a failed attempt.
        raise
    return {"received": True}


@app.get("/courses/{course_id}/access")
async def course_access(course_id: int, email: EmailStr, session: AsyncSession = Depends(get_session)) -> dict[str, bool]:
    student = await session.scalar(select(Student).where(Student.email == email.lower()))
    if student is None:
        return {"has_access": False}
    enrollment = await session.scalar(
        select(Enrollment).where(Enrollment.student_id == student.id, Enrollment.course_id == course_id)
    )
    return {"has_access": enrollment is not None}
