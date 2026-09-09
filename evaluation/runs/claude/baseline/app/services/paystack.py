"""Paystack API client and webhook signature verification.

Only the server ever holds the secret key. The client wraps the two calls we
need — initialize and verify — and `verify_signature` implements Paystack's
HMAC-SHA512 webhook check. `get_paystack` is a FastAPI dependency so tests can
override it with a fake (no network) while the real signature check still runs.
"""
from __future__ import annotations

import hashlib
import hmac

import httpx

from ..config import settings

_TIMEOUT = httpx.Timeout(30.0)


class PaystackError(RuntimeError):
    """Raised when Paystack returns a non-success response."""


class PaystackClient:
    def __init__(self, secret_key: str | None = None, base_url: str | None = None) -> None:
        self.secret_key = secret_key or settings.PAYSTACK_SECRET_KEY
        self.base_url = (base_url or settings.PAYSTACK_BASE_URL).rstrip("/")

    @property
    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self.secret_key}",
            "Content-Type": "application/json",
        }

    async def initialize_transaction(
        self,
        *,
        email: str,
        amount_kobo: int,
        reference: str,
        callback_url: str | None = None,
        metadata: dict | None = None,
    ) -> dict:
        """POST /transaction/initialize -> {authorization_url, access_code, reference}."""
        payload: dict = {
            "email": email,
            "amount": amount_kobo,  # smallest currency unit (e.g. kobo)
            "reference": reference,
        }
        if callback_url:
            payload["callback_url"] = callback_url
        if metadata:
            payload["metadata"] = metadata

        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            resp = await client.post(
                f"{self.base_url}/transaction/initialize",
                json=payload,
                headers=self._headers,
            )
        return self._unwrap(resp)

    async def verify_transaction(self, reference: str) -> dict:
        """GET /transaction/verify/:reference -> transaction data (status, amount, ...)."""
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            resp = await client.get(
                f"{self.base_url}/transaction/verify/{reference}",
                headers=self._headers,
            )
        return self._unwrap(resp)

    @staticmethod
    def _unwrap(resp: httpx.Response) -> dict:
        try:
            body = resp.json()
        except ValueError:
            raise PaystackError(f"Non-JSON response from Paystack (HTTP {resp.status_code})")
        if resp.status_code >= 400 or not body.get("status"):
            raise PaystackError(body.get("message", f"Paystack error (HTTP {resp.status_code})"))
        return body.get("data", {})


def verify_signature(
    raw_body: bytes, signature: str | None, secret: str | None = None
) -> bool:
    """Verify Paystack's `x-paystack-signature`: HMAC-SHA512 of the RAW body."""
    if not signature:
        return False
    key = (secret or settings.PAYSTACK_SECRET_KEY).encode("utf-8")
    computed = hmac.new(key, raw_body, hashlib.sha512).hexdigest()
    return hmac.compare_digest(computed, signature)


_client = PaystackClient()


def get_paystack() -> PaystackClient:
    """FastAPI dependency returning the shared Paystack client."""
    return _client
