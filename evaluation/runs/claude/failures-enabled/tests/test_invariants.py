"""System-level invariant checks (failure-checklist item 9: data consistency).

Rather than trusting any single code path, these tests drive a mixed workload
and then assert the global invariants hold across the *entire* database:

  I1  every enrollment traces to a COMPLETED payment for the same
      (student, course); no pending/failed payment ever has an enrollment.
  I2  at most one active (pending|completed) payment per (student, course),
      and at most one enrollment per (student, course).
"""
from __future__ import annotations

from sqlalchemy import select

from models import Enrollment, Payment, PaymentStatus
from services.payments import complete_payment, initialize_payment
from webhook.handler import handle_webhook


async def assert_consistent(session_factory) -> None:
    async with session_factory() as s:
        payments = list(await s.scalars(select(Payment)))
        enrollments = list(await s.scalars(select(Enrollment)))

    by_id = {p.id: p for p in payments}

    # I1: no enrollment without a completed, matching payment.
    for e in enrollments:
        p = by_id.get(e.payment_id)
        assert p is not None, f"enrollment {e.id} references missing payment"
        assert p.status is PaymentStatus.completed, (
            f"enrollment {e.id} points at non-completed payment {p.status}"
        )
        assert (p.student_id, p.course_id) == (e.student_id, e.course_id)

    # I1 (other direction): every completed payment has exactly one enrollment;
    # no non-completed payment has any.
    for p in payments:
        refs = [e for e in enrollments if e.payment_id == p.id]
        if p.status is PaymentStatus.completed:
            assert len(refs) == 1, f"completed payment {p.reference} has {len(refs)} enrollments"
        else:
            assert refs == [], f"non-completed payment {p.reference} is enrolled"

    # I2: at most one active payment per (student, course).
    active: dict[tuple[int, int], int] = {}
    for p in payments:
        if p.status in (PaymentStatus.pending, PaymentStatus.completed):
            key = (p.student_id, p.course_id)
            active[key] = active.get(key, 0) + 1
    assert all(n <= 1 for n in active.values()), f"multiple active payments: {active}"

    # I2: at most one enrollment per (student, course).
    seen: set[tuple[int, int]] = set()
    for e in enrollments:
        key = (e.student_id, e.course_id)
        assert key not in seen, f"duplicate enrollment for {key}"
        seen.add(key)


async def test_end_to_end_happy_path_via_api(
    client, fake_paystack, course, vr, charge_success_body
):
    # 1. student initializes payment
    resp = await client.post(
        "/payments/initialize",
        json={"student_id": 100, "email": "grad@test.io", "course_id": course.id},
        headers={"Idempotency-Key": "e2e-key"},
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["status"] == "pending"
    reference = data["reference"]

    # 2. Paystack later fires charge.success; we re-verify and it checks out.
    fake_paystack.set_verify(reference, vr(reference, amount=course.price))
    body = charge_success_body(reference, amount=course.price, txn_id=7001)
    hook = await client.post(
        "/webhooks/paystack", content=body,
        headers={"x-paystack-signature": fake_paystack.sign(body)},
    )
    assert hook.status_code == 200, hook.text

    # 3. student now has access
    status = await client.get(f"/payments/{reference}")
    body = status.json()
    assert body["status"] == "completed"
    assert body["enrolled"] is True


async def test_duplicate_initialize_via_api_charges_once(
    client, fake_paystack, course
):
    # Same Idempotency-Key twice through the HTTP layer -> same reference, one charge.
    payload = {"student_id": 101, "email": "x@test.io", "course_id": course.id}
    headers = {"Idempotency-Key": "e2e-dup"}
    r1 = await client.post("/payments/initialize", json=payload, headers=headers)
    r2 = await client.post("/payments/initialize", json=payload, headers=headers)
    assert r1.json()["reference"] == r2.json()["reference"]
    assert len(fake_paystack.init_calls) == 1


async def test_mixed_workload_preserves_invariants(
    session_factory, fake_paystack, course, make_pending, vr, charge_success_body
):
    # A: success via webhook
    a = await make_pending(course, student_id=200, reference="ref-A")
    fake_paystack.set_verify("ref-A", vr("ref-A", amount=course.price))
    body_a = charge_success_body("ref-A", amount=course.price, txn_id=8001)
    async with session_factory() as s:
        await handle_webhook(s, fake_paystack, raw_body=body_a,
                             signature=fake_paystack.sign(body_a))

    # B: declined -> failed, never enrolled
    b = await make_pending(course, student_id=201, reference="ref-B")
    fake_paystack.set_verify("ref-B", vr("ref-B", status="failed", amount=0))
    async with session_factory() as s:
        await complete_payment(s, fake_paystack, reference="ref-B", source="cb")

    # C: still pending (ambiguous, never verified) - left alone
    await make_pending(course, student_id=202, reference="ref-C")

    # D: duplicate webhook delivery -> still one enrollment
    await make_pending(course, student_id=203, reference="ref-D")
    fake_paystack.set_verify("ref-D", vr("ref-D", amount=course.price))
    body_d = charge_success_body("ref-D", amount=course.price, txn_id=8004)
    sig_d = fake_paystack.sign(body_d)
    for _ in range(2):
        async with session_factory() as s:
            await handle_webhook(s, fake_paystack, raw_body=body_d, signature=sig_d)

    await assert_consistent(session_factory)

    # spot-check the intended end states
    async with session_factory() as s:
        statuses = {
            p.reference: p.status
            for p in await s.scalars(select(Payment))
        }
    assert statuses["ref-A"] is PaymentStatus.completed
    assert statuses["ref-B"] is PaymentStatus.failed
    assert statuses["ref-C"] is PaymentStatus.pending
    assert statuses["ref-D"] is PaymentStatus.completed
