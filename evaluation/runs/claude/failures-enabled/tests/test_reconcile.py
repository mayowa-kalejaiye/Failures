"""Reconciliation worker: the recovery net for every ambiguous / lost outcome.

Failure-checklist items exercised:
  3. crash between Paystack success and enrollment -> a stale pending payment
     is driven to completed + enrolled on the next sweep.
  7. dependency still timing out -> stays pending, retried next pass (never a
     guess).

Time is controlled deterministically via explicit ``created_at`` values and the
``now`` argument, so no sleeping and no wall-clock flakiness.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sqlalchemy import func, select

from adapter import PaystackAmbiguousError, PaystackDefiniteError
from jobs.reconcile import reconcile_once
from models import Enrollment, Payment, PaymentStatus

BASE = datetime(2026, 1, 1, 12, 0, 0, tzinfo=timezone.utc)


async def _enrollments(session_factory, student_id, course_id) -> int:
    async with session_factory() as s:
        return await s.scalar(
            select(func.count()).select_from(Enrollment).where(
                Enrollment.student_id == student_id,
                Enrollment.course_id == course_id,
            )
        )


async def _status(session_factory, reference) -> PaymentStatus:
    async with session_factory() as s:
        p = await s.scalar(select(Payment).where(Payment.reference == reference))
        return p.status


async def test_recovers_stale_pending_to_completed(
    session_factory, fake_paystack, course, make_pending, vr, make_settings
):
    # Checklist #3: server crashed after Paystack charged but before we
    # recorded completion. The sweep settles it.
    await make_pending(course, student_id=20, reference="ref-stale", created_at=BASE)
    fake_paystack.set_verify("ref-stale", vr("ref-stale", amount=course.price))
    settings = make_settings(reconcile_min_age_seconds=0)

    async with session_factory() as s:
        summary = await reconcile_once(
            s, fake_paystack, settings, now=BASE + timedelta(seconds=300)
        )

    assert summary["completed"] == 1
    assert await _status(session_factory, "ref-stale") is PaymentStatus.completed
    assert await _enrollments(session_factory, 20, course.id) == 1


async def test_still_ambiguous_stays_pending(
    session_factory, fake_paystack, course, make_pending, make_settings
):
    # Checklist #7: Paystack still unreachable -> never guess, leave pending.
    await make_pending(course, student_id=21, reference="ref-amb", created_at=BASE)
    fake_paystack.set_verify("ref-amb", PaystackAmbiguousError("still down"))
    settings = make_settings(reconcile_min_age_seconds=0)

    async with session_factory() as s:
        summary = await reconcile_once(
            s, fake_paystack, settings, now=BASE + timedelta(seconds=300)
        )

    assert summary["ambiguous"] == 1
    assert await _status(session_factory, "ref-amb") is PaymentStatus.pending
    assert await _enrollments(session_factory, 21, course.id) == 0


async def test_aged_out_definite_error_is_abandoned(
    session_factory, fake_paystack, course, make_pending, make_settings
):
    # Paystack has no record and the payment is old enough that success is
    # implausible -> abandon (free the course), never enroll.
    await make_pending(course, student_id=22, reference="ref-old", created_at=BASE)
    fake_paystack.set_verify("ref-old", PaystackDefiniteError("no such txn", status_code=404))
    settings = make_settings(
        reconcile_min_age_seconds=0, reconcile_abandon_after_seconds=0
    )

    async with session_factory() as s:
        summary = await reconcile_once(
            s, fake_paystack, settings, now=BASE + timedelta(seconds=300)
        )

    assert summary["failed"] == 1
    assert await _status(session_factory, "ref-old") is PaymentStatus.failed


async def test_young_definite_error_is_left_pending(
    session_factory, fake_paystack, course, make_pending, make_settings
):
    # Definite error but the payment is still young -> don't abandon yet; a
    # delayed webhook could still arrive. Stays pending.
    await make_pending(course, student_id=23, reference="ref-young", created_at=BASE)
    fake_paystack.set_verify("ref-young", PaystackDefiniteError("not yet", status_code=404))
    settings = make_settings(
        reconcile_min_age_seconds=0, reconcile_abandon_after_seconds=3600
    )

    async with session_factory() as s:
        await reconcile_once(s, fake_paystack, settings, now=BASE + timedelta(seconds=60))

    assert await _status(session_factory, "ref-young") is PaymentStatus.pending


async def test_min_age_gate_skips_fresh_payments(
    session_factory, fake_paystack, course, make_pending, vr, make_settings
):
    # A freshly-created payment must be left for the webhook/callback first;
    # the reconciler should not race them.
    await make_pending(course, student_id=24, reference="ref-fresh", created_at=BASE)
    fake_paystack.set_verify("ref-fresh", vr("ref-fresh", amount=course.price))
    settings = make_settings(reconcile_min_age_seconds=120)

    async with session_factory() as s:
        summary = await reconcile_once(
            s, fake_paystack, settings, now=BASE + timedelta(seconds=30)
        )

    assert summary["scanned"] == 0
    assert fake_paystack.verify_calls == []
    assert await _status(session_factory, "ref-fresh") is PaymentStatus.pending


async def test_one_bad_row_does_not_stop_the_sweep(
    session_factory, fake_paystack, course, make_pending, vr, make_settings
):
    # Robustness: an unexpected error on one payment must not abort the batch.
    await make_pending(course, student_id=25, reference="ref-boom", created_at=BASE)
    await make_pending(course, student_id=26, reference="ref-good", created_at=BASE)
    fake_paystack.set_verify("ref-boom", ValueError("weird"))
    fake_paystack.set_verify("ref-good", vr("ref-good", amount=course.price))
    settings = make_settings(reconcile_min_age_seconds=0)

    async with session_factory() as s:
        summary = await reconcile_once(
            s, fake_paystack, settings, now=BASE + timedelta(seconds=300)
        )

    assert summary["completed"] == 1
    assert await _status(session_factory, "ref-good") is PaymentStatus.completed
    assert await _status(session_factory, "ref-boom") is PaymentStatus.pending
    assert await _enrollments(session_factory, 26, course.id) == 1
