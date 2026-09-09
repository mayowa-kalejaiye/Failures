"""Adapter-level failure classification.

The whole system's safety rests on the adapter drawing the right line between
an *ambiguous* outcome (timeout / network error / 5xx -> the charge MIGHT have
happened -> stay pending, reconcile) and a *definite* one (4xx -> Paystack
refused -> safe to stop). These tests pin that boundary, the retry count, and
the HMAC signature check.

Covers failure-checklist item 7 (dependency timeout) at the transport layer.
"""
from __future__ import annotations

import httpx
import pytest

from adapter import (
    PaystackAmbiguousError,
    PaystackClient,
    PaystackDefiniteError,
)


def _client(make_settings, handler, **over) -> PaystackClient:
    settings = make_settings(paystack_max_retries=2, paystack_timeout_seconds=1, **over)
    transport = httpx.MockTransport(handler)
    http = httpx.AsyncClient(transport=transport)
    pc = PaystackClient(settings=settings, client=http)

    async def _no_sleep(_attempt: int) -> None:  # keep retry tests instant
        return None

    pc._sleep_backoff = _no_sleep  # type: ignore[assignment]
    return pc


async def test_timeout_is_ambiguous_and_retried(make_settings):
    calls = {"n": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        calls["n"] += 1
        raise httpx.ReadTimeout("simulated hang", request=request)

    pc = _client(make_settings, handler)
    with pytest.raises(PaystackAmbiguousError):
        await pc.verify_transaction("ref_timeout")
    # max_retries=2 -> 3 total attempts; a timeout must never be a definite failure.
    assert calls["n"] == 3


async def test_5xx_is_ambiguous_and_retried(make_settings):
    calls = {"n": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        calls["n"] += 1
        return httpx.Response(502, text="bad gateway")

    pc = _client(make_settings, handler)
    with pytest.raises(PaystackAmbiguousError):
        await pc.verify_transaction("ref_5xx")
    assert calls["n"] == 3


async def test_4xx_is_definite_and_not_retried(make_settings):
    calls = {"n": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        calls["n"] += 1
        return httpx.Response(400, json={"status": False, "message": "bad ref"})

    pc = _client(make_settings, handler)
    with pytest.raises(PaystackDefiniteError) as exc:
        await pc.verify_transaction("ref_4xx")
    assert exc.value.status_code == 400
    assert calls["n"] == 1  # definite -> stop immediately, do not retry


async def test_verify_parses_success(make_settings):
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={
                "status": True,
                "data": {
                    "reference": "ref_ok",
                    "status": "success",
                    "amount": 500000,
                    "currency": "NGN",
                    "id": 998877,
                },
            },
        )

    pc = _client(make_settings, handler)
    result = await pc.verify_transaction("ref_ok")
    assert result.is_success is True
    assert result.amount == 500000
    assert result.currency == "NGN"
    assert result.transaction_id == "998877"


async def test_verify_reports_non_success_status(make_settings):
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={"status": True, "data": {"reference": "ref_fail",
                                            "status": "failed", "amount": 0}},
        )

    pc = _client(make_settings, handler)
    result = await pc.verify_transaction("ref_fail")
    assert result.is_success is False
    assert result.status == "failed"


async def test_initialize_recovers_after_transient_5xx(make_settings):
    """A single transient 5xx should be retried and then succeed - the caller
    never sees an error for a blip."""
    calls = {"n": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        calls["n"] += 1
        if calls["n"] == 1:
            return httpx.Response(503, text="try again")
        return httpx.Response(
            200,
            json={"status": True, "data": {
                "authorization_url": "https://checkout.test/x",
                "access_code": "acc_x", "reference": "ref_init"}},
        )

    pc = _client(make_settings, handler)
    out = await pc.initialize_transaction(
        email="s@test.io", amount=500000, reference="ref_init",
        idempotency_key="key_init",
    )
    assert out["authorization_url"] == "https://checkout.test/x"
    assert calls["n"] == 2


def test_signature_roundtrip(make_settings):
    pc = _client(make_settings, lambda r: httpx.Response(200, json={}))
    body = b'{"event":"charge.success","data":{"id":1}}'
    good = pc._headers  # noqa: F841  (keep import surface stable)
    import hashlib
    import hmac

    sig = hmac.new(pc.settings.paystack_secret_key.encode(), body, hashlib.sha512).hexdigest()
    assert pc.verify_signature(body, sig) is True
    assert pc.verify_signature(body, "deadbeef") is False
    assert pc.verify_signature(body, None) is False
