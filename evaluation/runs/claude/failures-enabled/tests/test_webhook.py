"""Webhook ingestion: verify signature -> dedup -> act (idempotently).

Failure-checklist item 4 (duplicate webhook delivery) is the headline here,
plus the safety properties that make redelivery correct:
  * an unsigned / wrongly-signed webhook is rejected before touching the DB;
  * a delivery whose processing crashed (processed_at IS NULL) is allowed to be
    retried, and the retry completes;
  * only charge.success grants access (I1) - other events are acknowledged for
    audit but never enroll.
"""
from __future__ import annotations

from sqlalchemy import func, select

from adapter import PaystackAmbiguousError
from models import Enrollment, PaymentStatus, WebhookEvent
from webhook.handler import InvalidSignatureError, handle_webhook


async def _enrollments(session_factory, student_id, course_id) -> int:
    async with session_factory() as s:
        return await s.scalar(
            select(func.count()).select_from(Enrollment).where(
                Enrollment.student_id == student_id,
                Enrollment.course_id == course_id,
            )
        )


async def _event(session_factory, event_id) -> WebhookEvent:
    async with session_factory() as s:
        return await s.scalar(
            select(WebhookEvent).where(WebhookEvent.event_id == event_id)
        )


async def test_valid_webhook_processes_and_enrolls(
    session_factory, fake_paystack, course, make_pending, vr, charge_success_body
):
    await make_pending(course, student_id=10, reference="ref-wh")
    fake_paystack.set_verify("ref-wh", vr("ref-wh", amount=course.price))
    body = charge_success_body("ref-wh", amount=course.price, txn_id=111)
    sig = fake_paystack.sign(body)

    async with session_factory() as s:
        out = await handle_webhook(s, fake_paystack, raw_body=body, signature=sig)

    assert out["status"] == "processed"
    assert await _enrollments(session_factory, 10, course.id) == 1
    ev = await _event(session_factory, "charge.success:111")
    assert ev is not None and ev.processed_at is not None


async def test_duplicate_delivery_is_deduped(
    session_factory, fake_paystack, course, make_pending, vr, charge_success_body
):
    # Checklist #4: Paystack delivers the same event twice. Second time is a
    # no-op: no re-verify, no second enrollment.
    await make_pending(course, student_id=11, reference="ref-dup")
    fake_paystack.set_verify("ref-dup", vr("ref-dup", amount=course.price))
    body = charge_success_body("ref-dup", amount=course.price, txn_id=222)
    sig = fake_paystack.sign(body)

    async with session_factory() as s:
        first = await handle_webhook(s, fake_paystack, raw_body=body, signature=sig)
    async with session_factory() as s:
        second = await handle_webhook(s, fake_paystack, raw_body=body, signature=sig)

    assert first["status"] == "processed"
    assert second["status"] == "duplicate"
    assert await _enrollments(session_factory, 11, course.id) == 1
    assert fake_paystack.verify_calls == ["ref-dup"]  # verified exactly once


async def test_invalid_signature_is_rejected_before_db(
    session_factory, fake_paystack, course, charge_success_body
):
    body = charge_success_body("ref-nosig", txn_id=333)
    async with session_factory() as s:
        try:
            await handle_webhook(s, fake_paystack, raw_body=body, signature="bogus")
            assert False, "expected InvalidSignatureError"
        except InvalidSignatureError:
            pass
    # Nothing recorded, nothing verified.
    assert await _event(session_factory, "charge.success:333") is None
    assert fake_paystack.verify_calls == []


async def test_crash_then_redelivery_recovers(
    session_factory, fake_paystack, course, make_pending, vr, charge_success_body
):
    # First delivery: verify is ambiguous -> handler raises, processed_at stays
    # NULL. Second delivery: Paystack healthy -> the retry completes. Exactly
    # one enrollment, event finally marked processed.
    await make_pending(course, student_id=12, reference="ref-crash")
    body = charge_success_body("ref-crash", amount=course.price, txn_id=444)
    sig = fake_paystack.sign(body)

    fake_paystack.set_verify("ref-crash", PaystackAmbiguousError("verify down"))
    async with session_factory() as s:
        try:
            await handle_webhook(s, fake_paystack, raw_body=body, signature=sig)
            assert False, "expected the ambiguous error to propagate"
        except PaystackAmbiguousError:
            pass

    ev = await _event(session_factory, "charge.success:444")
    assert ev is not None and ev.processed_at is None  # not marked done
    assert await _enrollments(session_factory, 12, course.id) == 0

    fake_paystack.set_verify("ref-crash", vr("ref-crash", amount=course.price))
    async with session_factory() as s:
        out = await handle_webhook(s, fake_paystack, raw_body=body, signature=sig)

    assert out["status"] == "processed"
    assert await _enrollments(session_factory, 12, course.id) == 1
    ev = await _event(session_factory, "charge.success:444")
    assert ev.processed_at is not None


async def test_non_success_event_is_acknowledged_without_enrolling(
    session_factory, fake_paystack, course, make_pending, charge_success_body
):
    # I1: a charge.failed event must never enroll, but is still recorded + acked
    # so Paystack stops retrying it.
    await make_pending(course, student_id=13, reference="ref-failed-evt")
    body = charge_success_body(
        "ref-failed-evt", event="charge.failed", status="failed", txn_id=555
    )
    sig = fake_paystack.sign(body)

    async with session_factory() as s:
        out = await handle_webhook(s, fake_paystack, raw_body=body, signature=sig)

    assert out["status"] == "processed"
    assert await _enrollments(session_factory, 13, course.id) == 0
    assert fake_paystack.verify_calls == []  # never even verified


async def test_api_rejects_unsigned_webhook(client, charge_success_body):
    # End-to-end through the FastAPI transport layer: 401, no redelivery-worthy 5xx.
    body = charge_success_body("ref-api-nosig", txn_id=666)
    resp = await client.post(
        "/webhooks/paystack", content=body,
        headers={"x-paystack-signature": "nope"},
    )
    assert resp.status_code == 401
