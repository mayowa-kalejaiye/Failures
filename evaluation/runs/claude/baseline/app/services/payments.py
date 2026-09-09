"""Payment finalization — the single, idempotent path that grants course access.

Webhook, browser callback, and the manual verify endpoint ALL funnel through
`finalize_payment`. It re-verifies the transaction with Paystack server-side
(never trusting a pushed payload), checks the amount + currency against the
course-price snapshot, and creates the enrollment exactly once. Calling it
repeatedly for the same reference is safe.
"""
from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from ..models import Enrollment, Payment, PaymentStatus
from .paystack import PaystackClient

# Paystack transaction statuses that are terminal but not successful.
_STATUS_MAP = {
    "failed": PaymentStatus.failed,
    "abandoned": PaymentStatus.abandoned,
    "reversed": PaymentStatus.failed,
}


class PaymentError(Exception):
    """Base class for finalization failures."""


class PaymentNotFound(PaymentError):
    pass


class PaymentNotSuccessful(PaymentError):
    def __init__(self, status: str) -> None:
        super().__init__(f"Transaction not successful (status={status})")
        self.status = status


class AmountMismatch(PaymentError):
    """The verified amount/currency does not match what we expected."""


def _parse_dt(value: str | None) -> datetime:
    if value:
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            pass
    return datetime.now(timezone.utc)


async def _ensure_enrollment(session: AsyncSession, payment: Payment) -> Enrollment:
    """Return the existing enrollment or create it, committing pending changes.

    Idempotent under concurrent finalize calls: the UNIQUE(user_id, course_id)
    constraint makes at most one enrollment win, and the loser adopts it. Uses a
    commit-level IntegrityError catch (portable across SQLite and PostgreSQL)
    rather than a SAVEPOINT.
    """
    existing = await session.scalar(
        select(Enrollment).where(
            Enrollment.user_id == payment.user_id,
            Enrollment.course_id == payment.course_id,
        )
    )
    if existing is not None:
        await session.commit()  # persist any pending payment changes
        return existing

    session.add(
        Enrollment(
            user_id=payment.user_id,
            course_id=payment.course_id,
            payment_id=payment.id,
        )
    )
    try:
        await session.commit()
    except IntegrityError:
        # A concurrent finalize created the enrollment first; adopt it.
        await session.rollback()

    enrollment = await session.scalar(
        select(Enrollment).where(
            Enrollment.user_id == payment.user_id,
            Enrollment.course_id == payment.course_id,
        )
    )
    if enrollment is None:  # pragma: no cover - constraint guarantees one exists
        raise RuntimeError("Enrollment missing after commit")
    return enrollment


async def finalize_payment(
    session: AsyncSession, paystack: PaystackClient, reference: str
) -> tuple[Payment, Enrollment]:
    """Verify a transaction and grant access. Idempotent per reference.

    Raises PaymentNotFound / PaymentNotSuccessful / AmountMismatch on failure.
    """
    payment = await session.scalar(
        select(Payment).where(Payment.reference == reference)
    )
    if payment is None:
        raise PaymentNotFound(reference)

    # Already finalized: just make sure access exists, then return.
    if payment.status == PaymentStatus.success:
        enrollment = await _ensure_enrollment(session, payment)
        return payment, enrollment

    data = await paystack.verify_transaction(reference)
    status = (data.get("status") or "").lower()

    if status != "success":
        payment.status = _STATUS_MAP.get(status, PaymentStatus.failed)
        payment.raw_response = data
        await session.commit()
        raise PaymentNotSuccessful(status or "unknown")

    # Defense in depth: the verified amount and currency MUST match the price
    # we snapshotted at checkout. Never trust a client- or webhook-supplied value.
    expected_kobo = int((payment.amount * 100).to_integral_value())
    paid_kobo = int(data.get("amount") or 0)
    paid_currency = (data.get("currency") or payment.currency).upper()

    if paid_kobo != expected_kobo or paid_currency != payment.currency.upper():
        payment.status = PaymentStatus.failed
        payment.raw_response = data
        await session.commit()
        raise AmountMismatch(
            f"expected {expected_kobo} {payment.currency}, got {paid_kobo} {paid_currency}"
        )

    payment.status = PaymentStatus.success
    payment.paid_at = _parse_dt(data.get("paid_at") or data.get("paidAt"))
    payment.raw_response = data
    enrollment = await _ensure_enrollment(session, payment)
    return payment, enrollment
