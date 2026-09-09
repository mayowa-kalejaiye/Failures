"""Payment orchestration - the correctness core of the system.

Two entry points:

* ``initialize_payment`` - create a durable ``pending`` payment and hand back a
  Paystack checkout URL. Ordering matters: the pending row is committed
  *before* we call Paystack, so a crash after Paystack succeeds still leaves a
  record for reconciliation to settle.

* ``complete_payment`` - the single, idempotent path that turns a pending
  payment into ``completed`` + an enrollment. Called by the webhook, the
  browser callback, and the reconciler alike. Whoever gets there first wins;
  everyone else is a no-op.
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from adapter import PaystackClient, VerificationResult
from models import Course, Payment, PaymentStatus
from models._ids import new_uuid
from services.enrollment import grant_enrollment
from services.errors import (
    AlreadyPaidError,
    CourseNotFoundError,
    PaymentAmountMismatchError,
)

log = logging.getLogger("payments")

_ACTIVE = (PaymentStatus.pending, PaymentStatus.completed)


def _now() -> datetime:
    return datetime.now(timezone.utc)


async def _find_by_idempotency_key(session: AsyncSession, key: str) -> Payment | None:
    return await session.scalar(
        select(Payment).where(Payment.idempotency_key == key)
    )


async def _find_active_for_course(
    session: AsyncSession, student_id: int, course_id: int
) -> Payment | None:
    return await session.scalar(
        select(Payment).where(
            Payment.student_id == student_id,
            Payment.course_id == course_id,
            Payment.status.in_(_ACTIVE),
        )
    )


async def initialize_payment(
    session: AsyncSession,
    paystack: PaystackClient,
    *,
    student_id: int,
    email: str,
    course_id: int,
    idempotency_key: str,
    callback_url: str | None = None,
) -> Payment:
    # (1) Exact-retry dedup. The same checkout attempt retried returns the same
    #     payment and its existing checkout URL - never a second charge (I2).
    existing = await _find_by_idempotency_key(session, idempotency_key)
    if existing is not None:
        return existing

    # (2) Course-level guard (fast path). At most one active payment per course.
    active = await _find_active_for_course(session, student_id, course_id)
    if active is not None:
        if active.status is PaymentStatus.completed:
            raise AlreadyPaidError(
                f"student {student_id} already paid for course {course_id}"
            )
        return active  # resume the pending checkout instead of starting a new one

    # Price is server-authoritative: the client never dictates the amount.
    course = await session.get(Course, course_id)
    if course is None:
        raise CourseNotFoundError(f"course {course_id} not found")

    # (3) Persist a durable pending row BEFORE the external call. If we crash
    #     between Paystack succeeding and the next line, this row is what lets
    #     reconciliation recover the payment.
    payment = Payment(
        reference=new_uuid(),
        idempotency_key=idempotency_key,
        student_id=student_id,
        course_id=course_id,
        amount=course.price,
        currency=course.currency,
        email=email,
        status=PaymentStatus.pending,
    )
    session.add(payment)
    try:
        await session.commit()
    except IntegrityError:
        # Lost a race on either UNIQUE(idempotency_key) or the active-per-course
        # index. Adopt whichever row the winner created (I2 under concurrency).
        await session.rollback()
        winner = await _find_by_idempotency_key(session, idempotency_key)
        if winner is None:
            winner = await _find_active_for_course(session, student_id, course_id)
        if winner is None:  # pragma: no cover - unexpected
            raise
        return winner

    # (4) Now the side-effecting external call. Retried internally with a stable
    #     reference, so it is idempotent on Paystack's side.
    try:
        init = await paystack.initialize_transaction(
            email=email,
            amount=payment.amount,
            reference=payment.reference,
            idempotency_key=idempotency_key,
            currency=payment.currency,
            callback_url=callback_url,
            metadata={"payment_id": payment.id, "course_id": course_id,
                      "student_id": student_id},
        )
    except Exception:
        # Ambiguous or definite - either way the pending row stays. On an
        # ambiguous error the transaction may actually exist on Paystack, so we
        # must NOT mark it failed here; reconciliation decides. We simply
        # surface the error and let the caller return a retryable response.
        log.warning("initialize failed for reference=%s; leaving pending",
                    payment.reference)
        raise

    payment.authorization_url = init["authorization_url"]
    payment.access_code = init["access_code"]
    await session.commit()
    return payment


async def complete_payment(
    session: AsyncSession,
    paystack: PaystackClient,
    *,
    reference: str,
    source: str,
) -> Payment | None:
    """Verify a transaction with Paystack and, if genuinely successful,
    atomically mark it completed and enroll the student.

    Idempotent and safe to call concurrently from webhook / callback /
    reconciler. Returns the payment, or None if the reference is unknown.

    ``source`` is only for logging/traceability.
    """
    # (A) Source of truth is Paystack, not the caller. We re-verify even for a
    #     signed webhook: it defends I1 (only enroll on a real success) against
    #     replayed or spoofed events. This is a GET, done OUTSIDE any DB
    #     transaction so we never hold a row lock across the network.
    result: VerificationResult = await paystack.verify_transaction(reference)

    # (B) The atomic unit: lock the payment row, and either flip
    #     pending -> completed AND create the enrollment together, or do
    #     nothing. Both writes commit or neither does (I1: no enrollment
    #     without a completed payment; no completed payment left un-enrolled).
    async with session.begin():
        payment = await session.scalar(
            select(Payment).where(Payment.reference == reference).with_for_update()
        )
        if payment is None:
            log.warning("[%s] webhook/verify for unknown reference=%s",
                        source, reference)
            return None

        # Idempotent: the first caller already completed it. The row lock
        # serialises concurrent callers, so exactly one performs the transition.
        if payment.status is PaymentStatus.completed:
            log.info("[%s] reference=%s already completed; no-op", source, reference)
            return payment

        if not result.is_success:
            # Definite decline/abandon -> mark failed (frees the course for a
            # legitimate retry). NEVER enroll (I1).
            if payment.status is PaymentStatus.pending:
                payment.status = PaymentStatus.failed
            log.info("[%s] reference=%s not successful (%s); marked failed",
                     source, reference, result.status)
            return payment

        # Success. Guard against a mismatched charge before granting access.
        if result.amount != payment.amount or result.currency != payment.currency:
            log.error(
                "[%s] AMOUNT MISMATCH reference=%s expected=%s%s got=%s%s - not enrolling",
                source, reference, payment.amount, payment.currency,
                result.amount, result.currency,
            )
            raise PaymentAmountMismatchError(reference)

        payment.status = PaymentStatus.completed
        payment.verified_at = _now()
        payment.paystack_transaction_id = result.transaction_id
        await grant_enrollment(
            session,
            student_id=payment.student_id,
            course_id=payment.course_id,
            payment_id=payment.id,
        )
        log.info("[%s] reference=%s completed and enrolled", source, reference)

    return payment
