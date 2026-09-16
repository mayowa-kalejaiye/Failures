"""Failure-safe incoming Paystack webhook handling with FastAPI and PostgreSQL.

Checkout must create the pending Payment row before it sends a customer to
Paystack. This endpoint only finalizes that existing record. Set DATABASE_URL
and PAYSTACK_SECRET_KEY before running.
"""

from __future__ import annotations

import asyncio
import hashlib
import hmac
import json
import os
import time
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Generator

import httpx
from fastapi import Depends, FastAPI, Header, HTTPException, Request, status
from sqlalchemy import DateTime, Integer, String, create_engine, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, sessionmaker


DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+psycopg://postgres:postgres@localhost/payments")
PAYSTACK_SECRET_KEY = os.getenv("PAYSTACK_SECRET_KEY", "")
PAYSTACK_BASE_URL = "https://api.paystack.co"


class Base(DeclarativeBase):
    pass


class PaymentStatus(str, Enum):
    PENDING = "pending"
    SUCCESS = "success"
    FAILED = "failed"


class Payment(Base):
    __tablename__ = "payments"
    id: Mapped[int] = mapped_column(primary_key=True)
    reference: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    customer_email: Mapped[str] = mapped_column(String(320))
    amount_minor: Mapped[int] = mapped_column(Integer)
    currency: Mapped[str] = mapped_column(String(3), default="NGN")
    status: Mapped[PaymentStatus] = mapped_column(default=PaymentStatus.PENDING)
    paystack_transaction_id: Mapped[str | None] = mapped_column(String(80), nullable=True)
    paid_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class WebhookEvent(Base):
    __tablename__ = "paystack_webhook_events"
    event_key: Mapped[str] = mapped_column(String(160), primary_key=True)
    received_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


class TokenBucket:
    def __init__(self, capacity: int = 120, refill_per_second: float = 2.0) -> None:
        self.capacity, self.refill_per_second = capacity, refill_per_second
        self.buckets: dict[str, tuple[float, float]] = {}
        self.lock = asyncio.Lock()

    async def consume(self, key: str) -> bool:
        async with self.lock:
            now = time.monotonic()
            tokens, updated = self.buckets.get(key, (float(self.capacity), now))
            tokens = min(self.capacity, tokens + (now - updated) * self.refill_per_second)
            self.buckets[key] = (tokens - 1, now) if tokens >= 1 else (tokens, now)
            return tokens >= 1


engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(engine, expire_on_commit=False)
limiter = TokenBucket()
app = FastAPI(title="Paystack webhook")


def get_session() -> Generator[Session, None, None]:
    with SessionLocal() as session:
        yield session


def paystack_headers() -> dict[str, str]:
    if not PAYSTACK_SECRET_KEY:
        raise HTTPException(status_code=500, detail="PAYSTACK_SECRET_KEY is not configured")
    return {"Authorization": f"Bearer {PAYSTACK_SECRET_KEY}"}


async def verify_transaction(reference: str) -> dict[str, Any]:
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            response = await client.get(f"{PAYSTACK_BASE_URL}/transaction/verify/{reference}", headers=paystack_headers())
            response.raise_for_status()
            payload = response.json()
    except (httpx.HTTPError, ValueError) as exc:
        raise HTTPException(status_code=502, detail="Could not verify payment with Paystack") from exc
    transaction = payload.get("data") if payload.get("status") else None
    if not isinstance(transaction, dict):
        raise HTTPException(status_code=502, detail="Invalid Paystack verification response")
    return transaction


@app.on_event("startup")
def create_tables() -> None:
    Base.metadata.create_all(engine)


@app.post("/webhooks/paystack", status_code=status.HTTP_200_OK)
async def paystack_webhook(
    request: Request,
    x_paystack_signature: str | None = Header(default=None),
    session: Session = Depends(get_session),
) -> dict[str, bool]:
    source = request.client.host if request.client else "unknown"
    if not await limiter.consume(source):
        raise HTTPException(status_code=429, detail="Too many webhook deliveries")
    raw_body = await request.body()
    expected = hmac.new(PAYSTACK_SECRET_KEY.encode(), raw_body, hashlib.sha512).hexdigest()
    if not PAYSTACK_SECRET_KEY or not x_paystack_signature or not hmac.compare_digest(expected, x_paystack_signature):
        raise HTTPException(status_code=401, detail="Invalid Paystack signature")
    try:
        event = json.loads(raw_body)
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=400, detail="Invalid webhook JSON") from exc

    event_name, data = event.get("event"), event.get("data", {})
    reference, transaction_id = data.get("reference"), data.get("id")
    if not isinstance(event_name, str) or not isinstance(reference, str) or transaction_id is None:
        raise HTTPException(status_code=400, detail="Webhook lacks transaction identity")
    event_key = f"{event_name}:{transaction_id}"

    # This marker is deliberately uncommitted until the corresponding payment update commits.
    inserted = session.execute(insert(WebhookEvent).values(event_key=event_key).on_conflict_do_nothing())
    if inserted.rowcount == 0:
        session.rollback()
        return {"received": True}

    try:
        payment = session.scalar(select(Payment).where(Payment.reference == reference).with_for_update())
        if payment is None:
            raise HTTPException(status_code=404, detail="Unknown payment reference")
        if data.get("amount") != payment.amount_minor or data.get("currency") != payment.currency:
            raise HTTPException(status_code=400, detail="Webhook amount or currency does not match")

        if event_name == "charge.success":
            verified = await verify_transaction(reference)
            verified_email = str(verified.get("customer", {}).get("email", "")).lower()
            valid = (
                verified.get("status") == "success"
                and verified.get("reference") == payment.reference
                and verified.get("amount") == payment.amount_minor
                and verified.get("currency") == payment.currency
                and verified_email == payment.customer_email.lower()
                and str(verified.get("id")) == str(transaction_id)
            )
            if not valid:
                raise HTTPException(status_code=400, detail="Paystack verification does not match local payment")
            payment.status = PaymentStatus.SUCCESS
            payment.paystack_transaction_id = str(transaction_id)
            payment.paid_at = datetime.now(timezone.utc)
        elif event_name in {"charge.failed", "charge.abandoned"}:
            # Never downgrade a verified success because delivery order is not guaranteed.
            if payment.status == PaymentStatus.PENDING:
                payment.status = PaymentStatus.FAILED

        session.commit()
    except Exception:
        session.rollback()  # A failed event remains eligible for Paystack redelivery.
        raise
    return {"received": True}
