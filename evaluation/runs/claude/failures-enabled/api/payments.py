"""Payment + enrollment HTTP endpoints."""
from __future__ import annotations

import logging
import uuid

from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from adapter import PaystackAmbiguousError, PaystackClient, PaystackDefiniteError
from api.deps import get_paystack
from config import get_settings
from db import get_session
from models import Enrollment, Payment
from schemas import (
    InitializePaymentRequest,
    InitializePaymentResponse,
    PaymentStatusResponse,
)
from services import payments as payment_service
from services.errors import AlreadyPaidError, CourseNotFoundError

log = logging.getLogger("api.payments")
router = APIRouter(prefix="/payments", tags=["payments"])


@router.post("/initialize", response_model=InitializePaymentResponse)
async def initialize_payment(
    body: InitializePaymentRequest,
    session: AsyncSession = Depends(get_session),
    paystack: PaystackClient = Depends(get_paystack),
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
):
    settings = get_settings()
    # Encourage clients to send their own key; if absent we generate one and
    # return it so a retry can reuse it. Without a reused key, a retry is a new
    # logical attempt (and the per-course guard still prevents a double charge).
    key = idempotency_key or f"gen_{uuid.uuid4()}"

    try:
        payment = await payment_service.initialize_payment(
            session,
            paystack,
            student_id=body.student_id,
            email=str(body.email),
            course_id=body.course_id,
            idempotency_key=key,
            callback_url=f"{settings.public_base_url}/payments/callback",
        )
    except CourseNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except AlreadyPaidError as exc:
        raise HTTPException(status_code=409, detail=str(exc))
    except PaystackDefiniteError as exc:
        raise HTTPException(status_code=502, detail=f"payment provider rejected: {exc}")
    except PaystackAmbiguousError:
        # Unknown outcome - a pending payment now exists and reconciliation will
        # settle it. Tell the client to retry with the SAME Idempotency-Key.
        raise HTTPException(
            status_code=503,
            detail="payment provider did not respond in time; retry with the "
                   "same Idempotency-Key",
            headers={"Retry-After": "5", "Idempotency-Key": key},
        )

    return InitializePaymentResponse(
        payment_id=payment.id,
        reference=payment.reference,
        status=payment.status,
        authorization_url=payment.authorization_url,
        idempotency_key=payment.idempotency_key,
    )


@router.get("/callback")
async def payment_callback(
    reference: str,
    session: AsyncSession = Depends(get_session),
    paystack: PaystackClient = Depends(get_paystack),
):
    """Browser return URL after Paystack checkout. A synchronous fallback to the
    webhook: verifies and completes immediately so the student sees access
    without waiting for the async webhook. Idempotent - it shares
    complete_payment with the webhook and the reconciler."""
    try:
        payment = await payment_service.complete_payment(
            session, paystack, reference=reference, source="callback"
        )
    except PaystackAmbiguousError:
        return {"status": "processing",
                "detail": "we are confirming your payment; access will be "
                          "granted shortly"}
    if payment is None:
        raise HTTPException(status_code=404, detail="unknown payment reference")
    return {"status": payment.status.value, "reference": payment.reference}


@router.get("/{reference}", response_model=PaymentStatusResponse)
async def get_payment(
    reference: str,
    session: AsyncSession = Depends(get_session),
):
    payment = await session.scalar(
        select(Payment).where(Payment.reference == reference)
    )
    if payment is None:
        raise HTTPException(status_code=404, detail="unknown payment reference")
    enrolled = await session.scalar(
        select(Enrollment).where(
            Enrollment.student_id == payment.student_id,
            Enrollment.course_id == payment.course_id,
        )
    )
    return PaymentStatusResponse(
        payment_id=payment.id,
        reference=payment.reference,
        status=payment.status,
        course_id=payment.course_id,
        student_id=payment.student_id,
        enrolled=enrolled is not None,
    )
