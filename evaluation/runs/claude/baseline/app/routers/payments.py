"""Payment routes: checkout, Paystack webhook, browser callback, manual verify."""
import logging
from typing import Annotated
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..config import settings
from ..core.security import CurrentUser
from ..database import get_session
from ..models import Course, Enrollment, Payment, PaymentStatus
from ..schemas import CheckoutOut, PaymentResultOut
from ..services.paystack import PaystackClient, PaystackError, get_paystack, verify_signature
from ..services.payments import (
    AmountMismatch,
    PaymentNotFound,
    PaymentNotSuccessful,
    finalize_payment,
)

logger = logging.getLogger(__name__)

router = APIRouter(tags=["payments"])

SessionDep = Annotated[AsyncSession, Depends(get_session)]
PaystackDep = Annotated[PaystackClient, Depends(get_paystack)]


def _reference(course_id: int, user_id: int) -> str:
    return f"crs-{course_id}-{user_id}-{uuid4().hex}"


def _result(payment: Payment, enrolled: bool, message: str) -> PaymentResultOut:
    return PaymentResultOut(
        reference=payment.reference,
        status=payment.status,
        enrolled=enrolled,
        course_id=payment.course_id,
        message=message,
    )


@router.post(
    "/courses/{course_id}/checkout",
    response_model=CheckoutOut,
    status_code=status.HTTP_201_CREATED,
    tags=["courses"],
)
async def checkout(
    course_id: int, session: SessionDep, paystack: PaystackDep, user: CurrentUser
) -> CheckoutOut:
    course = await session.get(Course, course_id)
    if course is None or not course.is_published:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Course not found")

    already = await session.scalar(
        select(Enrollment).where(
            Enrollment.user_id == user.id, Enrollment.course_id == course_id
        )
    )
    if already is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="You already have access to this course",
        )

    # Server computes the amount and generates the reference — the client never
    # supplies a price. Amount goes to Paystack in the smallest unit (kobo).
    amount_kobo = int((course.price * 100).to_integral_value())
    reference = _reference(course_id, user.id)

    payment = Payment(
        reference=reference,
        user_id=user.id,
        course_id=course.id,
        amount=course.price,
        currency=course.currency.upper(),
        status=PaymentStatus.pending,
    )
    session.add(payment)
    await session.flush()

    try:
        data = await paystack.initialize_transaction(
            email=user.email,
            amount_kobo=amount_kobo,
            reference=reference,
            callback_url=settings.PAYSTACK_CALLBACK_URL,
            metadata={
                "payment_id": payment.id,
                "course_id": course.id,
                "user_id": user.id,
            },
        )
    except PaystackError as exc:
        # Nothing is committed, so the pending row is rolled back on session close.
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Could not initialize payment: {exc}",
        )

    payment.authorization_url = data.get("authorization_url")
    payment.access_code = data.get("access_code")
    await session.commit()

    return CheckoutOut(
        authorization_url=payment.authorization_url,
        reference=reference,
        payment_id=payment.id,
        amount=course.price,
        currency=payment.currency,
    )


@router.post("/webhooks/paystack", include_in_schema=True)
async def paystack_webhook(
    request: Request, session: SessionDep, paystack: PaystackDep
) -> dict:
    """Paystack -> us. Signature-verified; the reliable source of truth for access."""
    raw = await request.body()
    signature = request.headers.get("x-paystack-signature")
    if not verify_signature(raw, signature):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid signature"
        )

    event = await request.json()
    if event.get("event") == "charge.success":
        reference = (event.get("data") or {}).get("reference")
        if reference:
            try:
                await finalize_payment(session, paystack, reference)
            except PaymentNotFound:
                logger.warning("Webhook for unknown reference: %s", reference)
            except (PaymentNotSuccessful, AmountMismatch) as exc:
                # Do NOT grant access; retrying won't change the verified data.
                logger.error("Webhook finalize rejected for %s: %s", reference, exc)

    # Always 200 once the signature is valid so Paystack stops retrying.
    return {"status": "ok"}


@router.get("/payments/callback", response_model=PaymentResultOut, tags=["payments"])
async def payment_callback(
    session: SessionDep,
    paystack: PaystackDep,
    reference: str | None = None,
    trxref: str | None = None,
) -> PaymentResultOut:
    """Where Paystack redirects the browser after checkout (UX + local-dev fallback)."""
    ref = reference or trxref
    if not ref:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Missing payment reference"
        )
    return await _finalize_and_describe(session, paystack, ref)


@router.get(
    "/payments/{reference}/verify", response_model=PaymentResultOut, tags=["payments"]
)
async def verify_payment(
    reference: str, session: SessionDep, paystack: PaystackDep, user: CurrentUser
) -> PaymentResultOut:
    """Auth'd endpoint a frontend can poll to confirm access was granted."""
    payment = await session.scalar(select(Payment).where(Payment.reference == reference))
    if payment is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Payment not found")
    if payment.user_id != user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not your payment")
    return await _finalize_and_describe(session, paystack, reference)


async def _finalize_and_describe(
    session: AsyncSession, paystack: PaystackClient, reference: str
) -> PaymentResultOut:
    try:
        payment, _enrollment = await finalize_payment(session, paystack, reference)
    except PaymentNotFound:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Payment not found")
    except PaymentNotSuccessful as exc:
        payment = await session.scalar(
            select(Payment).where(Payment.reference == reference)
        )
        return _result(payment, False, f"Payment not completed: {exc.status}")
    except AmountMismatch as exc:
        payment = await session.scalar(
            select(Payment).where(Payment.reference == reference)
        )
        return _result(payment, False, f"Payment amount mismatch — access not granted ({exc})")

    return _result(payment, True, f"Payment successful — you now have access to course {payment.course_id}")
