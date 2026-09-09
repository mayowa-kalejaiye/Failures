"""Paystack HTTP client.

Design rules that keep the caller safe under failure:

* **Every call is bounded by a timeout.** A hung dependency must not pin a
  worker forever.
* **A timeout / network error / 5xx is an *ambiguous* outcome, not a
  failure.** We raise ``PaystackAmbiguousError`` for these. The caller must
  NOT conclude "the payment failed" - the charge may well have succeeded. It
  leaves state pending and lets reconciliation settle it.
* **A 4xx is a *definite* failure** (``PaystackDefiniteError``) - Paystack
  understood the request and refused it. Safe to stop.
* **Retries are bounded and only applied to idempotent calls.** We always send
  a stable ``reference`` (and an ``Idempotency-Key`` header), so re-sending an
  ``initialize`` returns the same transaction rather than creating a new one.
  Backoff has jitter to avoid a retry storm.
"""
from __future__ import annotations

import asyncio
import hashlib
import hmac
import logging
import random
from dataclasses import dataclass, field

import httpx

from config import Settings, get_settings

log = logging.getLogger("paystack")


class PaystackError(Exception):
    """Base class for all Paystack adapter errors."""


class PaystackAmbiguousError(PaystackError):
    """Outcome is unknown (timeout, network error, 5xx). NOT a failure.

    The operation may have succeeded on Paystack's side. Callers must preserve
    pending state and reconcile rather than treating this as a decline."""


class PaystackDefiniteError(PaystackError):
    """Paystack definitively rejected the request (4xx)."""

    def __init__(self, message: str, status_code: int | None = None) -> None:
        super().__init__(message)
        self.status_code = status_code


@dataclass
class VerificationResult:
    reference: str
    status: str  # "success" | "failed" | "abandoned" | ...
    amount: int  # subunit
    currency: str
    transaction_id: str | None
    raw: dict = field(default_factory=dict)

    @property
    def is_success(self) -> bool:
        return self.status == "success"


class PaystackClient:
    def __init__(
        self,
        settings: Settings | None = None,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        self.settings = settings or get_settings()
        self._client = client  # injected & reused in the app; created per-call otherwise
        self._timeout = httpx.Timeout(self.settings.paystack_timeout_seconds)

    # -- low level ---------------------------------------------------------
    def _headers(self, idempotency_key: str | None) -> dict[str, str]:
        headers = {
            "Authorization": f"Bearer {self.settings.paystack_secret_key}",
            "Content-Type": "application/json",
        }
        if idempotency_key:
            headers["Idempotency-Key"] = idempotency_key
        return headers

    async def _sleep_backoff(self, attempt: int) -> None:
        # exponential backoff capped at 2s, plus jitter to avoid a thundering herd
        delay = min(0.2 * (2 ** attempt), 2.0) + random.uniform(0, 0.2)
        await asyncio.sleep(delay)

    async def _request(
        self,
        method: str,
        path: str,
        *,
        json: dict | None = None,
        idempotency_key: str | None = None,
    ) -> dict:
        url = f"{self.settings.paystack_base_url}{path}"
        attempts = self.settings.paystack_max_retries + 1
        last_error: Exception | None = None

        for attempt in range(attempts):
            try:
                if self._client is not None:
                    resp = await self._client.request(
                        method, url, json=json,
                        headers=self._headers(idempotency_key), timeout=self._timeout,
                    )
                else:
                    async with httpx.AsyncClient(timeout=self._timeout) as client:
                        resp = await client.request(
                            method, url, json=json,
                            headers=self._headers(idempotency_key),
                        )
            except (httpx.TimeoutException, httpx.TransportError) as exc:
                # Ambiguous: request may have been received & processed.
                last_error = exc
                log.warning("paystack %s %s attempt %d ambiguous: %r",
                            method, path, attempt + 1, exc)
                if attempt + 1 < attempts:
                    await self._sleep_backoff(attempt)
                continue

            if resp.status_code >= 500:
                # Server error - also ambiguous, also retryable.
                last_error = PaystackAmbiguousError(
                    f"{resp.status_code} from Paystack: {resp.text[:200]}"
                )
                log.warning("paystack %s %s attempt %d -> %d", method, path,
                            attempt + 1, resp.status_code)
                if attempt + 1 < attempts:
                    await self._sleep_backoff(attempt)
                continue

            if resp.status_code >= 400:
                # Definite client-side rejection: do not retry.
                raise PaystackDefiniteError(
                    f"{resp.status_code} from Paystack: {resp.text[:200]}",
                    status_code=resp.status_code,
                )

            return resp.json()

        # Retries exhausted while the outcome stayed unknown.
        raise PaystackAmbiguousError(
            f"exhausted {attempts} attempts for {method} {path}: {last_error!r}"
        )

    # -- operations --------------------------------------------------------
    async def initialize_transaction(
        self,
        *,
        email: str,
        amount: int,
        reference: str,
        idempotency_key: str,
        currency: str = "NGN",
        callback_url: str | None = None,
        metadata: dict | None = None,
    ) -> dict:
        body: dict = {
            "email": email,
            "amount": amount,
            "reference": reference,  # stable => idempotent re-initialise
            "currency": currency,
            "metadata": metadata or {},
        }
        if callback_url:
            body["callback_url"] = callback_url
        data = await self._request(
            "POST", "/transaction/initialize",
            json=body, idempotency_key=idempotency_key,
        )
        payload = data.get("data", {})
        return {
            "authorization_url": payload.get("authorization_url"),
            "access_code": payload.get("access_code"),
            "reference": payload.get("reference", reference),
        }

    async def verify_transaction(self, reference: str) -> VerificationResult:
        # GET is naturally idempotent; safe to retry on ambiguity.
        data = await self._request("GET", f"/transaction/verify/{reference}")
        payload = data.get("data", {}) or {}
        txn_id = payload.get("id")
        return VerificationResult(
            reference=payload.get("reference", reference),
            status=payload.get("status", "unknown"),
            amount=int(payload.get("amount", 0) or 0),
            currency=payload.get("currency", "NGN"),
            transaction_id=str(txn_id) if txn_id is not None else None,
            raw=payload,
        )

    # -- webhook signature -------------------------------------------------
    def verify_signature(self, raw_body: bytes, signature: str | None) -> bool:
        """Paystack signs the raw body with HMAC-SHA512 using the secret key.

        Compared in constant time to avoid a timing side-channel."""
        if not signature:
            return False
        computed = hmac.new(
            self.settings.paystack_secret_key.encode("utf-8"),
            raw_body,
            hashlib.sha512,
        ).hexdigest()
        return hmac.compare_digest(computed, signature)
