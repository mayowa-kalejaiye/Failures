"""initialize_payment: the durable-pending-before-external-call path.

Failure-checklist items exercised here:
  1. duplicate request         -> same idempotency_key returns the same payment
  2. ambiguous external outcome -> pending row survives an init timeout
  6. retry after timeout        -> retry with same key resumes, never re-charges

Invariant I2 (never charged twice) is asserted structurally: at most one
active payment per (student, course), and a repeat never produces a second
Paystack initialize call.
"""
from __future__ import annotations

import pytest
from sqlalchemy import func, select

from adapter import PaystackAmbiguousError
from models import Payment, PaymentStatus
from services.errors import AlreadyPaidError, CourseNotFoundError
from services.payments import initialize_payment


async def _count_payments(session_factory) -> int:
    async with session_factory() as s:
        return await s.scalar(select(func.count()).select_from(Payment))


async def test_initialize_creates_pending_before_external_call(
    session_factory, fake_paystack, course
):
    async with session_factory() as s:
        payment = await initialize_payment(
            s, fake_paystack,
            student_id=1, email="s@test.io", course_id=course.id,
            idempotency_key="key-1",
        )
    assert payment.status is PaymentStatus.pending
    # Amount comes from the course, never the caller (server-authoritative price).
    assert payment.amount == course.price
    assert payment.authorization_url == f"https://checkout.test/{payment.reference}"
    assert len(fake_paystack.init_calls) == 1


async def test_duplicate_request_same_key_is_deduped(
    session_factory, fake_paystack, course
):
    # Checklist #1 + #6: same logical attempt twice -> ONE payment, ONE charge.
    async with session_factory() as s:
        first = await initialize_payment(
            s, fake_paystack, student_id=1, email="s@test.io",
            course_id=course.id, idempotency_key="key-dup",
        )
    async with session_factory() as s:
        second = await initialize_payment(
            s, fake_paystack, student_id=1, email="s@test.io",
            course_id=course.id, idempotency_key="key-dup",
        )

    assert first.id == second.id
    assert first.reference == second.reference
    assert await _count_payments(session_factory) == 1
    assert len(fake_paystack.init_calls) == 1  # no second charge


async def test_ambiguous_initialize_leaves_durable_pending(
    session_factory, fake_paystack, course
):
    # Checklist #2: Paystack init is ambiguous (timeout). We must NOT mark the
    # payment failed - the transaction may exist on Paystack's side. The pending
    # row must persist so reconciliation can settle it.
    fake_paystack.init_behavior = PaystackAmbiguousError("timeout")

    async with session_factory() as s:
        with pytest.raises(PaystackAmbiguousError):
            await initialize_payment(
                s, fake_paystack, student_id=1, email="s@test.io",
                course_id=course.id, idempotency_key="key-amb",
            )

    async with session_factory() as s:
        row = await s.scalar(
            select(Payment).where(Payment.idempotency_key == "key-amb")
        )
    assert row is not None, "pending row must survive an ambiguous init"
    assert row.status is PaymentStatus.pending  # not 'failed'


async def test_retry_after_ambiguous_reuses_same_payment(
    session_factory, fake_paystack, course
):
    # Checklist #6: after the ambiguous init above, the student retries with the
    # SAME key. It must resume the existing pending payment, not open a second.
    fake_paystack.init_behavior = PaystackAmbiguousError("timeout")
    async with session_factory() as s:
        with pytest.raises(PaystackAmbiguousError):
            await initialize_payment(
                s, fake_paystack, student_id=1, email="s@test.io",
                course_id=course.id, idempotency_key="key-retry",
            )

    fake_paystack.init_behavior = None  # Paystack is healthy on retry
    async with session_factory() as s:
        resumed = await initialize_payment(
            s, fake_paystack, student_id=1, email="s@test.io",
            course_id=course.id, idempotency_key="key-retry",
        )

    assert resumed.idempotency_key == "key-retry"
    assert await _count_payments(session_factory) == 1


async def test_second_course_attempt_without_key_is_blocked_when_active(
    session_factory, fake_paystack, course
):
    # Even with a *different* idempotency key, a second concurrent attempt for
    # the same (student, course) must not open a second active payment (I2).
    async with session_factory() as s:
        await initialize_payment(
            s, fake_paystack, student_id=7, email="s@test.io",
            course_id=course.id, idempotency_key="key-a",
        )
    async with session_factory() as s:
        resumed = await initialize_payment(
            s, fake_paystack, student_id=7, email="s@test.io",
            course_id=course.id, idempotency_key="key-b",
        )
    # resumes the existing pending payment rather than creating a new one
    assert resumed.idempotency_key == "key-a"
    assert await _count_payments(session_factory) == 1


async def test_already_completed_course_rejects_new_payment(
    session_factory, fake_paystack, course, make_pending
):
    # A completed payment for this course already exists -> charging again would
    # break I2. initialize must refuse.
    await make_pending(
        course, student_id=9, idempotency_key="key-done",
        status=PaymentStatus.completed,
    )
    async with session_factory() as s:
        with pytest.raises(AlreadyPaidError):
            await initialize_payment(
                s, fake_paystack, student_id=9, email="s@test.io",
                course_id=course.id, idempotency_key="key-new",
            )


async def test_unknown_course_is_rejected(session_factory, fake_paystack):
    async with session_factory() as s:
        with pytest.raises(CourseNotFoundError):
            await initialize_payment(
                s, fake_paystack, student_id=1, email="s@test.io",
                course_id=999999, idempotency_key="key-x",
            )
    # No charge attempted for a course that does not exist.
    assert fake_paystack.init_calls == []
