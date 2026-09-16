"""
Paystack payment webhook.

Receives charge events and updates payment status in PostgreSQL.
Paystack may resend the same event.
"""

import hashlib
import hmac
import json
import os
from datetime import datetime
from typing import Any, Optional

from fastapi import Depends, FastAPI, Header, HTTPException, Request
from sqlalchemy import Column, DateTime, Integer, String, create_engine
from sqlalchemy.orm import Session, declarative_base, sessionmaker

DATABASE_URL = os.getenv(
    "DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/webhooks"
)
PAYSTACK_SECRET_KEY = os.getenv("PAYSTACK_SECRET_KEY", "sk_test_replace_me")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()
app = FastAPI(title="Paystack webhook")


class Payment(Base):
    __tablename__ = "payments"

    id = Column(Integer, primary_key=True)
    reference = Column(String, unique=True, nullable=False, index=True)
    status = Column(String, nullable=False, default="pending")
    amount = Column(Integer, nullable=True)
    customer_email = Column(String, nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)


def verify_signature(body: bytes, signature: Optional[str]) -> None:
    if not signature:
        raise HTTPException(status_code=401, detail="Missing Paystack signature")
    expected = hmac.new(
        PAYSTACK_SECRET_KEY.encode("utf-8"), body, hashlib.sha512
    ).hexdigest()
    if not hmac.compare_digest(expected, signature):
        raise HTTPException(status_code=401, detail="Invalid Paystack signature")


def status_from_event(event: str, data: dict[str, Any]) -> str:
    if event in ("charge.success", "charge.completed"):
        return "success"
    if event in ("charge.failed", "charge.abandoned"):
        return "failed"
    gateway = (data.get("status") or "").lower()
    if gateway in ("success", "failed", "abandoned", "pending"):
        return gateway
    return "pending"


@app.post("/webhooks/paystack")
async def paystack_webhook(
    request: Request,
    db: Session = Depends(get_db),
    x_paystack_signature: Optional[str] = Header(default=None),
):
    body = await request.body()
    verify_signature(body, x_paystack_signature)
    payload = json.loads(body.decode("utf-8"))

    event = payload.get("event") or ""
    data = payload.get("data") or {}
    reference = data.get("reference")
    if not reference:
        raise HTTPException(status_code=400, detail="Missing payment reference")

    payment = db.query(Payment).filter(Payment.reference == reference).first()
    new_status = status_from_event(event, data)
    if not payment:
        payment = Payment(
            reference=reference,
            status=new_status,
            amount=data.get("amount"),
            customer_email=(data.get("customer") or {}).get("email"),
        )
        db.add(payment)
    else:
        payment.status = new_status
        payment.amount = data.get("amount", payment.amount)
        payment.updated_at = datetime.utcnow()

    db.commit()
    return {"ok": True, "reference": reference, "status": payment.status}
