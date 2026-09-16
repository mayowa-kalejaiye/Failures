"""Paystack webhook endpoint with PostgreSQL-backed duplicate-event handling.

Set DATABASE_URL and PAYSTACK_SECRET_KEY. Paystack signs the exact request body
with HMAC-SHA512; never accept a webhook based on its JSON payload alone.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import os
from datetime import datetime, timezone
from enum import Enum
from typing import Generator

from fastapi import Depends, FastAPI, Header, HTTPException, Request, status
from sqlalchemy import DateTime, Integer, String, create_engine, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, sessionmaker


DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+psycopg://postgres:postgres@localhost/payments")
PAYSTACK_SECRET_KEY = os.getenv("PAYSTACK_SECRET_KEY", "")


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
    amount_minor: Mapped[int] = mapped_column(Integer)
    currency: Mapped[str] = mapped_column(String(3), default="NGN")
    status: Mapped[PaymentStatus] = mapped_column(default=PaymentStatus.PENDING)
    paystack_transaction_id: Mapped[str | None] = mapped_column(String(80), nullable=True)
    paid_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class WebhookEvent(Base):
    __tablename__ = "paystack_webhook_events"
    event_key: Mapped[str] = mapped_column(String(160), primary_key=True)
    received_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(engine, expire_on_commit=False)
app = FastAPI(title="Paystack webhook")


def get_session() -> Generator[Session, None, None]:
    with SessionLocal() as session:
        yield session


@app.on_event("startup")
def create_tables() -> None:
    Base.metadata.create_all(engine)


@app.post("/webhooks/paystack", status_code=status.HTTP_200_OK)
async def paystack_webhook(
    request: Request,
    x_paystack_signature: str | None = Header(default=None),
    session: Session = Depends(get_session),
) -> dict[str, bool]:
    raw_body = await request.body()
    expected = hmac.new(PAYSTACK_SECRET_KEY.encode(), raw_body, hashlib.sha512).hexdigest()
    if not PAYSTACK_SECRET_KEY or not x_paystack_signature or not hmac.compare_digest(expected, x_paystack_signature):
        raise HTTPException(status_code=401, detail="Invalid Paystack signature")
    try:
        event = json.loads(raw_body)
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=400, detail="Invalid webhook JSON") from exc

    event_name = event.get("event")
    data = event.get("data", {})
    transaction_id = data.get("id")
    reference = data.get("reference")
    if not isinstance(event_name, str) or transaction_id is None or not isinstance(reference, str):
        raise HTTPException(status_code=400, detail="Webhook lacks payment identity")

    event_key = f"{event_name}:{transaction_id}"
    inserted = session.execute(insert(WebhookEvent).values(event_key=event_key).on_conflict_do_nothing())
    if inserted.rowcount == 0:
        session.rollback()
        return {"received": True}

    payment = session.scalar(select(Payment).where(Payment.reference == reference).with_for_update())
    if payment is None:
        session.rollback()  # Do not retain a marker for an unknown payment; retries may arrive after creation.
        raise HTTPException(status_code=404, detail="Unknown payment reference")

    # Do not trust amounts from the event for fulfillment; only update a matching local payment.
    if data.get("amount") != payment.amount_minor or data.get("currency") != payment.currency:
        session.rollback()
        raise HTTPException(status_code=400, detail="Payment fields do not match")
    if event_name == "charge.success":
        payment.status = PaymentStatus.SUCCESS
        payment.paystack_transaction_id = str(transaction_id)
        payment.paid_at = datetime.now(timezone.utc)
    elif event_name in {"charge.failed", "charge.abandoned"} and payment.status == PaymentStatus.PENDING:
        payment.status = PaymentStatus.FAILED
    session.commit()  # Event marker and payment update are one transaction.
    return {"received": True}
