"""Course checkout and automatic enrollment with FastAPI, PostgreSQL, and Paystack.

Set DATABASE_URL and PAYSTACK_SECRET_KEY before running this module.  Amounts are
stored in the smallest currency unit (kobo for NGN) so that no floating point
values are involved in a payment decision.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import os
import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Any

import httpx
from fastapi import Depends, FastAPI, Header, HTTPException, Request, status
from pydantic import BaseModel, EmailStr, Field, HttpUrl
from sqlalchemy import DateTime, ForeignKey, Integer, String, UniqueConstraint, select
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://postgres:postgres@localhost/courses")
PAYSTACK_SECRET_KEY = os.getenv("PAYSTACK_SECRET_KEY", "")
PAYSTACK_BASE_URL = "https://api.paystack.co"


class Base(DeclarativeBase):
    pass


class PaymentStatus(str, Enum):
    pending = "pending"
    succeeded = "succeeded"
    failed = "failed"


class Student(Base):
    __tablename__ = "students"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(320), unique=True, index=True)


class Course(Base):
    __tablename__ = "courses"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(200))
    price_minor: Mapped[int] = mapped_column(Integer)  # kobo, cents, etc.
    currency: Mapped[str] = mapped_column(String(3), default="NGN")
    is_published: Mapped[bool] = mapped_column(default=True)


class Payment(Base):
    __tablename__ = "payments"

    id: Mapped[int] = mapped_column(primary_key=True)
    reference: Mapped[str] = mapped_column(String(80), unique=True, index=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("students.id"), index=True)
    course_id: Mapped[int] = mapped_column(ForeignKey("courses.id"), index=True)
    amount_minor: Mapped[int] = mapped_column(Integer)
    currency: Mapped[str] = mapped_column(String(3))
    status: Mapped[PaymentStatus] = mapped_column(default=PaymentStatus.pending)
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


# The driver is intentionally loaded at application startup.  This keeps
# command-line tools (OpenAPI generation, migrations, and unit-test imports)
# usable on machines that do not have asyncpg installed yet.
engine: AsyncEngine | None = None
SessionLocal: async_sessionmaker[AsyncSession] | None = None
app = FastAPI(title="Course payments")


async def get_session() -> AsyncSession:
    if SessionLocal is None:
        raise HTTPException(status_code=503, detail="Database is not initialized")
    async with SessionLocal() as session:
        yield session


class CheckoutRequest(BaseModel):
    email: EmailStr
    course_id: int
    callback_url: HttpUrl | None = None


class CheckoutResponse(BaseModel):
    reference: str
    authorization_url: str


def paystack_headers() -> dict[str, str]:
    if not PAYSTACK_SECRET_KEY:
        raise HTTPException(status_code=500, detail="PAYSTACK_SECRET_KEY is not configured")
    return {"Authorization": f"Bearer {PAYSTACK_SECRET_KEY}"}


async def paystack_initialize(payment: Payment, student: Student, callback_url: HttpUrl | None) -> str:
    payload: dict[str, Any] = {
        "email": student.email,
        "amount": payment.amount_minor,
        "currency": payment.currency,
        "reference": payment.reference,
    }
    if callback_url:
        payload["callback_url"] = str(callback_url)
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            response = await client.post(f"{PAYSTACK_BASE_URL}/transaction/initialize", headers=paystack_headers(), json=payload)
            response.raise_for_status()
            body = response.json()
    except (httpx.HTTPError, ValueError) as exc:
        raise HTTPException(status_code=502, detail="Could not initialize payment") from exc
    if not body.get("status") or not body.get("data", {}).get("authorization_url"):
        raise HTTPException(status_code=502, detail="Paystack rejected payment initialization")
    return body["data"]["authorization_url"]


async def paystack_verify(reference: str) -> dict[str, Any]:
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            response = await client.get(f"{PAYSTACK_BASE_URL}/transaction/verify/{reference}", headers=paystack_headers())
            response.raise_for_status()
            body = response.json()
    except (httpx.HTTPError, ValueError) as exc:
        raise HTTPException(status_code=502, detail="Could not verify payment") from exc
    if not body.get("status") or not isinstance(body.get("data"), dict):
        raise HTTPException(status_code=502, detail="Invalid verification response from Paystack")
    return body["data"]


async def fulfill_verified_payment(session: AsyncSession, reference: str) -> Payment:
    """Verify at Paystack, then atomically mark paid and create the enrollment."""
    transaction = await paystack_verify(reference)
    payment = await session.scalar(select(Payment).where(Payment.reference == reference).with_for_update())
    if payment is None:
        raise HTTPException(status_code=404, detail="Unknown payment reference")

    student = await session.get(Student, payment.student_id)
    expected_email = student.email.lower() if student else ""
    received_email = str(transaction.get("customer", {}).get("email", "")).lower()
    is_valid = (
        transaction.get("status") == "success"
        and transaction.get("reference") == payment.reference
        and transaction.get("amount") == payment.amount_minor
        and transaction.get("currency") == payment.currency
        and received_email == expected_email
    )
    if not is_valid:
        if transaction.get("status") in {"failed", "abandoned", "reversed"}:
            payment.status = PaymentStatus.failed
            await session.commit()
        raise HTTPException(status_code=400, detail="Payment has not been successfully verified")

    if payment.status != PaymentStatus.succeeded:
        payment.status = PaymentStatus.succeeded
        payment.paystack_transaction_id = str(transaction.get("id"))
        payment.paid_at = datetime.now(timezone.utc)

    enrollment = await session.scalar(
        select(Enrollment).where(Enrollment.student_id == payment.student_id, Enrollment.course_id == payment.course_id)
    )
    if enrollment is None:
        session.add(Enrollment(student_id=payment.student_id, course_id=payment.course_id, payment_id=payment.id))
    await session.commit()
    await session.refresh(payment)
    return payment


@app.on_event("startup")
async def create_tables() -> None:
    # Use Alembic migrations in a production deployment; useful for a standalone demo.
    global engine, SessionLocal
    engine = create_async_engine(DATABASE_URL, pool_pre_ping=True)
    SessionLocal = async_sessionmaker(engine, expire_on_commit=False)
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)


@app.post("/checkout", response_model=CheckoutResponse, status_code=status.HTTP_201_CREATED)
async def checkout(data: CheckoutRequest, session: AsyncSession = Depends(get_session)) -> CheckoutResponse:
    course = await session.get(Course, data.course_id)
    if course is None or not course.is_published:
        raise HTTPException(status_code=404, detail="Course not found")
    if course.price_minor <= 0:
        raise HTTPException(status_code=400, detail="Course price must be positive")

    student = await session.scalar(select(Student).where(Student.email == data.email.lower()))
    if student is None:
        student = Student(email=data.email.lower())
        session.add(student)
        await session.flush()
    payment = Payment(
        reference=f"course_{uuid.uuid4().hex}",
        student_id=student.id,
        course_id=course.id,
        amount_minor=course.price_minor,
        currency=course.currency,
    )
    session.add(payment)
    await session.commit()
    try:
        authorization_url = await paystack_initialize(payment, student, data.callback_url)
    except HTTPException:
        # Keep the pending attempt for reconciliation/audit rather than silently losing it.
        raise
    return CheckoutResponse(reference=payment.reference, authorization_url=authorization_url)


@app.get("/payments/{reference}/verify")
async def verify_payment(reference: str, session: AsyncSession = Depends(get_session)) -> dict[str, str]:
    payment = await fulfill_verified_payment(session, reference)
    return {"reference": payment.reference, "status": payment.status.value, "message": "Enrollment active"}


@app.post("/paystack/webhook", status_code=status.HTTP_200_OK)
async def paystack_webhook(
    request: Request,
    x_paystack_signature: str | None = Header(default=None),
    session: AsyncSession = Depends(get_session),
) -> dict[str, bool]:
    raw_body = await request.body()
    expected = hmac.new(PAYSTACK_SECRET_KEY.encode(), raw_body, hashlib.sha512).hexdigest()
    if not PAYSTACK_SECRET_KEY or not x_paystack_signature or not hmac.compare_digest(expected, x_paystack_signature):
        raise HTTPException(status_code=401, detail="Invalid Paystack signature")
    try:
        event = json.loads(raw_body)
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=400, detail="Invalid webhook JSON") from exc
    if event.get("event") == "charge.success":
        reference = event.get("data", {}).get("reference")
        if isinstance(reference, str):
            await fulfill_verified_payment(session, reference)
    return {"received": True}


@app.get("/courses/{course_id}/access")
async def course_access(course_id: int, email: EmailStr, session: AsyncSession = Depends(get_session)) -> dict[str, bool]:
    """Example authorization check for course-content endpoints."""
    student = await session.scalar(select(Student).where(Student.email == email.lower()))
    if student is None:
        return {"has_access": False}
    enrollment = await session.scalar(
        select(Enrollment).where(Enrollment.student_id == student.id, Enrollment.course_id == course_id)
    )
    return {"has_access": enrollment is not None}
