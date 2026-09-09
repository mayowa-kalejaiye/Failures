"""Tests for the payment + enrollment flow, including the security-critical paths:
signature verification, idempotency, and amount-tampering defense."""
import json
from decimal import Decimal


async def _checkout(client, headers, course_id):
    resp = await client.post(f"/courses/{course_id}/checkout", headers=headers)
    assert resp.status_code == 201, resp.text
    return resp.json()


def _charge_success_body(reference, amount_kobo=500000, currency="NGN"):
    return json.dumps(
        {
            "event": "charge.success",
            "data": {
                "reference": reference,
                "amount": amount_kobo,
                "currency": currency,
                "status": "success",
            },
        }
    ).encode()


async def _post_webhook(client, sign_webhook, raw, signature=None):
    sig = signature if signature is not None else sign_webhook(raw)
    return await client.post(
        "/webhooks/paystack", content=raw, headers={"x-paystack-signature": sig}
    )


async def _content_status(client, headers, course_id):
    return (await client.get(f"/courses/{course_id}/content", headers=headers)).status_code


async def test_checkout_returns_authorization_url(client, course, make_auth_headers):
    headers = await make_auth_headers()
    data = await _checkout(client, headers, course.id)
    assert data["authorization_url"].startswith("https://checkout.paystack.com/")
    assert data["reference"]
    assert Decimal(str(data["amount"])) == course.price
    assert data["currency"] == "NGN"


async def test_checkout_requires_auth(client, course):
    resp = await client.post(f"/courses/{course.id}/checkout")
    assert resp.status_code == 401


async def test_webhook_grants_access(client, course, make_auth_headers, sign_webhook):
    headers = await make_auth_headers()
    # No access before paying.
    assert await _content_status(client, headers, course.id) == 403

    data = await _checkout(client, headers, course.id)
    resp = await _post_webhook(client, sign_webhook, _charge_success_body(data["reference"]))
    assert resp.status_code == 200

    # Access granted automatically after the verified payment.
    content = await client.get(f"/courses/{course.id}/content", headers=headers)
    assert content.status_code == 200
    assert content.json()["content"] == "THE SECRET COURSE MATERIAL"

    enrollments = await client.get("/me/enrollments", headers=headers)
    assert enrollments.status_code == 200
    assert len(enrollments.json()) == 1
    assert enrollments.json()[0]["course_id"] == course.id


async def test_webhook_invalid_signature_rejected(
    client, course, make_auth_headers, sign_webhook
):
    headers = await make_auth_headers()
    data = await _checkout(client, headers, course.id)

    resp = await _post_webhook(
        client, sign_webhook, _charge_success_body(data["reference"]),
        signature="deadbeef-not-a-valid-signature",
    )
    assert resp.status_code == 401
    # No access was granted.
    assert await _content_status(client, headers, course.id) == 403


async def test_webhook_missing_signature_rejected(
    client, course, make_auth_headers
):
    headers = await make_auth_headers()
    data = await _checkout(client, headers, course.id)
    resp = await client.post(
        "/webhooks/paystack", content=_charge_success_body(data["reference"])
    )
    assert resp.status_code == 401


async def test_webhook_is_idempotent(client, course, make_auth_headers, sign_webhook):
    headers = await make_auth_headers()
    data = await _checkout(client, headers, course.id)
    raw = _charge_success_body(data["reference"])

    # Deliver the same event three times.
    for _ in range(3):
        assert (await _post_webhook(client, sign_webhook, raw)).status_code == 200

    enrollments = await client.get("/me/enrollments", headers=headers)
    assert len(enrollments.json()) == 1  # exactly one enrollment, no duplicates


async def test_amount_tampering_denies_access(
    client, course, make_auth_headers, sign_webhook, fake_paystack
):
    headers = await make_auth_headers()
    data = await _checkout(client, headers, course.id)

    # Simulate Paystack verifying a DIFFERENT (smaller) amount than the course price.
    fake_paystack.amount_override = 100  # 1.00 NGN instead of 5000.00

    resp = await _post_webhook(client, sign_webhook, _charge_success_body(data["reference"]))
    assert resp.status_code == 200  # acknowledged, but...
    # ...access is NOT granted because the verified amount didn't match.
    assert await _content_status(client, headers, course.id) == 403
    enrollments = await client.get("/me/enrollments", headers=headers)
    assert enrollments.json() == []


async def test_checkout_conflicts_when_already_enrolled(
    client, course, make_auth_headers, sign_webhook
):
    headers = await make_auth_headers()
    data = await _checkout(client, headers, course.id)
    await _post_webhook(client, sign_webhook, _charge_success_body(data["reference"]))

    # Second checkout for a course the student already owns.
    resp = await client.post(f"/courses/{course.id}/checkout", headers=headers)
    assert resp.status_code == 409


async def test_verify_endpoint_grants_access(client, course, make_auth_headers):
    headers = await make_auth_headers()
    data = await _checkout(client, headers, course.id)

    resp = await client.get(f"/payments/{data['reference']}/verify", headers=headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["enrolled"] is True
    assert body["status"] == "success"
    assert await _content_status(client, headers, course.id) == 200


async def test_verify_rejects_other_users_payment(client, course, make_auth_headers):
    owner = await make_auth_headers(email="owner@test.com")
    data = await _checkout(client, owner, course.id)

    attacker = await make_auth_headers(email="attacker@test.com")
    resp = await client.get(f"/payments/{data['reference']}/verify", headers=attacker)
    assert resp.status_code == 403
