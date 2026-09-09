"""complete_payment: verify -> (atomically) mark completed + enroll.

This is where invariants I1 and I2 are enforced, so it gets the most scrutiny.

  I1  a student is never enrolled without a *successful, amount-matching*
      verified payment.
  I2  the pending -> completed transition (and the enrollment it authorises)
      happens at most once, even under retries / concurrency.

Failure-checklist items exercised: 3 (crash between states, via re-run),
5 (concurrent execution), 8 (partial failure: DB error after Paystack success).
"""
from __future__ import annotations

import asyncio

import pytest
from sqlalchemy import func, select

from models import Enrollment, Payment, PaymentStatus
from services.errors import PaymentAmountMismatchError
from services.payments import complete_payment


async def _enrollment_count(session_factory, student_id, course_id) -> int:
    async with session_factory() as s:
        return await s.scalar(
            select(func.count()).select_from(Enrollment).where(
                Enrollment.student_id == student_id,
                Enrollment.course_id == course_id,
            )
        )


async def _reload(session_factory, reference) -> Payment:
    async with session_factory() as s:
        return await s.scalar(select(Payment).where(Payment.reference == reference))


async def test_success_completes_and_enrolls(
    session_factory, fake_paystack, course, make_pending, vr
):
    p = await make_pending(course, student_id=1, reference="ref-ok")
    fake_paystack.set_verify("ref-ok", vr("ref-ok", amount=course.price))

    async with session_factory() as s:
        result = await complete_payment(
            s, fake_paystack, reference="ref-ok", source="test"
        )
    assert result.status is PaymentStatus.completed
    assert result.verified_at is not None
    assert result.paystack_transaction_id == "txn_1"
    assert await _enrollment_count(session_factory, 1, course.id) == 1


async def test_double_complete_is_idempotent(
    session_factory, fake_paystack, course, make_pending, vr
):
    # Checklist #3 recovery shape: calling the shared path twice (e.g. webhook
    # then reconciler) enrolls exactly once.
    await make_pending(course, student_id=2, reference="ref-idem")
    fake_paystack.set_verify("ref-idem", vr("ref-idem", amount=course.price))

    async with session_factory() as s:
        await complete_payment(s, fake_paystack, reference="ref-idem", source="a")
    async with session_factory() as s:
        again = await complete_payment(s, fake_paystack, reference="ref-idem", source="b")

    assert again.status is PaymentStatus.completed
    assert await _enrollment_count(session_factory, 2, course.id) == 1


async def test_failed_verification_never_enrolls(
    session_factory, fake_paystack, course, make_pending, vr
):
    # I1: Paystack says the charge failed -> mark failed, never enroll.
    await make_pending(course, student_id=3, reference="ref-decline")
    fake_paystack.set_verify("ref-decline", vr("ref-decline", status="failed", amount=0))

    async with session_factory() as s:
        result = await complete_payment(
            s, fake_paystack, reference="ref-decline", source="test"
        )
    assert result.status is PaymentStatus.failed
    assert await _enrollment_count(session_factory, 3, course.id) == 0


async def test_amount_mismatch_is_refused(
    session_factory, fake_paystack, course, make_pending, vr
):
    # I1: Paystack reports success but for the WRONG amount -> do not enroll.
    await make_pending(course, student_id=4, reference="ref-mismatch")
    fake_paystack.set_verify(
        "ref-mismatch", vr("ref-mismatch", amount=course.price - 1)
    )

    async with session_factory() as s:
        with pytest.raises(PaymentAmountMismatchError):
            await complete_payment(
                s, fake_paystack, reference="ref-mismatch", source="test"
            )

    row = await _reload(session_factory, "ref-mismatch")
    assert row.status is PaymentStatus.pending  # not completed
    assert await _enrollment_count(session_factory, 4, course.id) == 0


async def test_partial_failure_after_success_rolls_back_atomically(
    session_factory, fake_paystack, course, make_pending, vr, monkeypatch
):
    # Checklist #8: Paystack verify succeeds, but the DB write for the
    # enrollment blows up. The completed-flip and the enrollment must roll back
    # TOGETHER: we must never be left with a completed payment and no
    # enrollment (or vice versa). Reconciliation will retry later.
    await make_pending(course, student_id=5, reference="ref-partial")
    fake_paystack.set_verify("ref-partial", vr("ref-partial", amount=course.price))

    async def boom(*args, **kwargs):
        raise RuntimeError("database exploded mid-enrollment")

    monkeypatch.setattr("services.payments.grant_enrollment", boom)

    async with session_factory() as s:
        with pytest.raises(RuntimeError):
            await complete_payment(
                s, fake_paystack, reference="ref-partial", source="test"
            )

    row = await _reload(session_factory, "ref-partial")
    assert row.status is PaymentStatus.pending, "status flip must roll back with enrollment"
    assert row.verified_at is None
    assert await _enrollment_count(session_factory, 5, course.id) == 0


async def test_concurrent_completes_enroll_exactly_once(
    session_factory, fake_paystack, course, make_pending, vr
):
    # Checklist #5: two callers (say webhook + callback) race to complete the
    # same payment. Exactly one enrollment may result (I2 / concurrency).
    await make_pending(course, student_id=6, reference="ref-race")
    fake_paystack.set_verify("ref-race", vr("ref-race", amount=course.price))

    async def run():
        async with session_factory() as s:
            return await complete_payment(
                s, fake_paystack, reference="ref-race", source="race"
            )

    results = await asyncio.gather(run(), run(), run(), return_exceptions=True)
    # None of the racers should surface an error to the user.
    errors = [r for r in results if isinstance(r, Exception)]
    assert not errors, f"concurrent completion raised: {errors!r}"

    assert await _enrollment_count(session_factory, 6, course.id) == 1
    row = await _reload(session_factory, "ref-race")
    assert row.status is PaymentStatus.completed


async def test_unknown_reference_is_noop(session_factory, fake_paystack, vr):
    fake_paystack.set_verify("ref-ghost", vr("ref-ghost"))
    async with session_factory() as s:
        result = await complete_payment(
            s, fake_paystack, reference="ref-ghost", source="test"
        )
    assert result is None
