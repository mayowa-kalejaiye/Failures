

# ============================================================
# SOURCE: models\payment.py
# ============================================================

import enum
from datetime import datetime

from sqlalchemy import (
    BigInteger,
    DateTime,
    Enum as SAEnum,
    Index,
    Integer,
    String,
    func,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column

from db import Base
from models._ids import new_uuid


class PaymentStatus(str, enum.Enum):
    # A payment is a small state machine. The transition pending -> completed
    # happens exactly once, under a row lock, which is the core of I2.
    pending = "pending"
    completed = "completed"
    failed = "failed"


class Payment(Base):
    __tablename__ = "payments"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)

    # Our own reference, sent to Paystack as `reference`. Because it is stable,
    # re-initialising / re-verifying with it is idempotent on Paystack's side,
    # and it is the join key between our record and the transaction.
    reference: Mapped[str] = mapped_column(
        String(64), unique=True, index=True, default=new_uuid, nullable=False
    )

    # Client-supplied key that identifies one logical checkout attempt.
    # UNIQUE => the same attempt retried never creates a second charge (I2).
    idempotency_key: Mapped[str] = mapped_column(
        String(128), unique=True, nullable=False
    )

    student_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    course_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)

    # Amount is in the currency subunit (kobo for NGN). Sourced from the
    # course, never the client - the client cannot tell us what to charge.
    amount: Mapped[int] = mapped_column(BigInteger, nullable=False)
    currency: Mapped[str] = mapped_column(String(8), nullable=False, default="NGN")
    email: Mapped[str] = mapped_column(String(255), nullable=False)

    status: Mapped[PaymentStatus] = mapped_column(
        SAEnum(PaymentStatus, native_enum=False, create_constraint=False,
               length=16, validate_strings=True),
        nullable=False,
        default=PaymentStatus.pending,
        index=True,
    )

    authorization_url: Mapped[str | None] = mapped_column(String(512))
    access_code: Mapped[str | None] = mapped_column(String(128))
    paystack_transaction_id: Mapped[str | None] = mapped_column(String(64))

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
    verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    __table_args__ = (
        # At most ONE active (pending or completed) payment may exist per
        # (student, course). This is the invariant backstop for I2 at the
        # business level: two concurrent "pay for course X" requests cannot
        # both create a charge - one wins the insert, the other is told to
        # resume the existing one. A `failed` row is excluded, so a genuine
        # retry-after-failure is still allowed.
        Index(
            "uq_active_payment_per_course",
            "student_id",
            "course_id",
            unique=True,
            postgresql_where=text("status IN ('pending', 'completed')"),
            sqlite_where=text("status IN ('pending', 'completed')"),
        ),
    )

    def __repr__(self) -> str:  # pragma: no cover - debug aid
        return (
            f"<Payment {self.reference} student={self.student_id} "
            f"course={self.course_id} status={self.status}>"
        )


# ============================================================
# SOURCE: models\enrollment.py
# ============================================================

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from db import Base
from models._ids import new_uuid


class Enrollment(Base):
    """Grants a student access to a course.

    ``UNIQUE(student_id, course_id)`` makes the grant idempotent: a duplicate
    webhook, a retry, or the reconciler racing the webhook can all *attempt*
    to enroll, but only one row can ever exist (I2 / concurrency).

    ``payment_id`` records *which* verified payment authorised access, so every
    enrollment is traceable back to a completed payment (I1).
    """

    __tablename__ = "enrollments"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    student_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    course_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    payment_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("payments.id"), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    __table_args__ = (
        UniqueConstraint("student_id", "course_id", name="uq_enrollment_student_course"),
    )


# ============================================================
# SOURCE: models\course.py
# ============================================================

from datetime import datetime

from sqlalchemy import BigInteger, DateTime, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from db import Base


class Course(Base):
    """Minimal course catalogue. The price lives here so the amount charged is
    server-authoritative - a client can ask to enroll, never to set the fee."""

    __tablename__ = "courses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    # Subunit of the currency (kobo for NGN), matching Paystack's convention.
    price: Mapped[int] = mapped_column(BigInteger, nullable=False)
    currency: Mapped[str] = mapped_column(String(8), nullable=False, default="NGN")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


# ============================================================
# SOURCE: models\webhook_event.py
# ============================================================

from datetime import datetime

from sqlalchemy import JSON, DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column

from db import Base
from models._ids import new_uuid


class WebhookEvent(Base):
    """Ledger of received Paystack webhooks, used for deduplication.

    ``event_id`` is UNIQUE. Paystack does not send a dedicated delivery UUID,
    so we derive a stable id from ``<event>:<data.id>`` (see webhook/handler.py):
    the same charge redelivered maps to the same id and is rejected as a
    duplicate.

    ``processed_at`` is nullable on purpose. The row is inserted *before* the
    payment is completed; it is stamped only once processing succeeds. So a
    delivery whose processing crashed (processed_at IS NULL) is allowed to be
    retried by Paystack, while a fully-handled one is fast-pathed. The true
    idempotency guarantee still lives in complete_payment(); this table is the
    audit trail + fast-path dedup, not the sole defence.
    """

    __tablename__ = "webhook_events"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    event_id: Mapped[str] = mapped_column(String(128), unique=True, nullable=False)
    event_type: Mapped[str] = mapped_column(String(64), nullable=False)
    reference: Mapped[str | None] = mapped_column(String(64), index=True)
    payload: Mapped[dict] = mapped_column(JSON, nullable=False)
    received_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    processed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


# ============================================================
# SOURCE: services\payments.py
# ============================================================

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


# ============================================================
# SOURCE: services\enrollment.py
# ============================================================

"""Idempotent enrollment grant."""
from __future__ import annotations

import logging

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from models import Enrollment

log = logging.getLogger("enrollment")


async def grant_enrollment(
    session: AsyncSession,
    *,
    student_id: int,
    course_id: int,
    payment_id: str,
) -> Enrollment:
    """Grant access, idempotently.

    Must be called *inside* an already-open transaction (it is part of the
    same atomic unit as marking the payment completed). We first look for an
    existing enrollment, then insert inside a SAVEPOINT so that a lost race on
    the UNIQUE(student, course) constraint rolls back only the insert - not the
    caller's whole transaction - and we return the winning row.
    """
    existing = await session.scalar(
        select(Enrollment).where(
            Enrollment.student_id == student_id,
            Enrollment.course_id == course_id,
        )
    )
    if existing is not None:
        return existing

    enrollment = Enrollment(
        student_id=student_id, course_id=course_id, payment_id=payment_id
    )
    session.add(enrollment)
    try:
        async with session.begin_nested():  # SAVEPOINT
            await session.flush()
    except IntegrityError:
        # A concurrent grant won the unique constraint; adopt its row.
        log.info("enrollment race for student=%s course=%s; using existing",
                 student_id, course_id)
        existing = await session.scalar(
            select(Enrollment).where(
                Enrollment.student_id == student_id,
                Enrollment.course_id == course_id,
            )
        )
        if existing is None:  # pragma: no cover - should be unreachable
            raise
        return existing
    return enrollment


# ============================================================
# SOURCE: services\errors.py
# ============================================================

class ServiceError(Exception):
    """Base class for domain-level errors raised by the service layer."""


class CourseNotFoundError(ServiceError):
    pass


class AlreadyPaidError(ServiceError):
    """A completed payment (and therefore enrollment) already exists for this
    student + course. Charging again would violate I2."""


class PaymentAmountMismatchError(ServiceError):
    """Paystack reported success, but for a different amount/currency than the
    order. We must not grant access to a mismatched charge (I1)."""


# ============================================================
# SOURCE: adapter\paystack.py
# ============================================================

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


# ============================================================
# SOURCE: api\payments.py
# ============================================================

"""Payment + enrollment HTTP endpoints."""
from __future__ import annotations

import logging
import uuid

from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from adapter import PaystackAmbiguousError, PaystackClient, PaystackDefiniteError
from api.deps import get_paystack
from config import get_settings
from db import get_session
from models import Enrollment, Payment
from schemas import (
    InitializePaymentRequest,
    InitializePaymentResponse,
    PaymentStatusResponse,
)
from services import payments as payment_service
from services.errors import AlreadyPaidError, CourseNotFoundError

log = logging.getLogger("api.payments")
router = APIRouter(prefix="/payments", tags=["payments"])


@router.post("/initialize", response_model=InitializePaymentResponse)
async def initialize_payment(
    body: InitializePaymentRequest,
    session: AsyncSession = Depends(get_session),
    paystack: PaystackClient = Depends(get_paystack),
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
):
    settings = get_settings()
    # Encourage clients to send their own key; if absent we generate one and
    # return it so a retry can reuse it. Without a reused key, a retry is a new
    # logical attempt (and the per-course guard still prevents a double charge).
    key = idempotency_key or f"gen_{uuid.uuid4()}"

    try:
        payment = await payment_service.initialize_payment(
            session,
            paystack,
            student_id=body.student_id,
            email=str(body.email),
            course_id=body.course_id,
            idempotency_key=key,
            callback_url=f"{settings.public_base_url}/payments/callback",
        )
    except CourseNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except AlreadyPaidError as exc:
        raise HTTPException(status_code=409, detail=str(exc))
    except PaystackDefiniteError as exc:
        raise HTTPException(status_code=502, detail=f"payment provider rejected: {exc}")
    except PaystackAmbiguousError:
        # Unknown outcome - a pending payment now exists and reconciliation will
        # settle it. Tell the client to retry with the SAME Idempotency-Key.
        raise HTTPException(
            status_code=503,
            detail="payment provider did not respond in time; retry with the "
                   "same Idempotency-Key",
            headers={"Retry-After": "5", "Idempotency-Key": key},
        )

    return InitializePaymentResponse(
        payment_id=payment.id,
        reference=payment.reference,
        status=payment.status,
        authorization_url=payment.authorization_url,
        idempotency_key=payment.idempotency_key,
    )


@router.get("/callback")
async def payment_callback(
    reference: str,
    session: AsyncSession = Depends(get_session),
    paystack: PaystackClient = Depends(get_paystack),
):
    """Browser return URL after Paystack checkout. A synchronous fallback to the
    webhook: verifies and completes immediately so the student sees access
    without waiting for the async webhook. Idempotent - it shares
    complete_payment with the webhook and the reconciler."""
    try:
        payment = await payment_service.complete_payment(
            session, paystack, reference=reference, source="callback"
        )
    except PaystackAmbiguousError:
        return {"status": "processing",
                "detail": "we are confirming your payment; access will be "
                          "granted shortly"}
    if payment is None:
        raise HTTPException(status_code=404, detail="unknown payment reference")
    return {"status": payment.status.value, "reference": payment.reference}


@router.get("/{reference}", response_model=PaymentStatusResponse)
async def get_payment(
    reference: str,
    session: AsyncSession = Depends(get_session),
):
    payment = await session.scalar(
        select(Payment).where(Payment.reference == reference)
    )
    if payment is None:
        raise HTTPException(status_code=404, detail="unknown payment reference")
    enrolled = await session.scalar(
        select(Enrollment).where(
            Enrollment.student_id == payment.student_id,
            Enrollment.course_id == payment.course_id,
        )
    )
    return PaymentStatusResponse(
        payment_id=payment.id,
        reference=payment.reference,
        status=payment.status,
        course_id=payment.course_id,
        student_id=payment.student_id,
        enrolled=enrolled is not None,
    )


# ============================================================
# SOURCE: api\webhooks.py
# ============================================================

"""Paystack webhook endpoint.

Thin transport layer: read the raw body (needed for signature verification),
delegate to ``webhook.handler``, and translate the outcome into a status code.
A processing error becomes a 5xx on purpose - that is the signal for Paystack
to redeliver later, which together with the reconciler guarantees the payment
is eventually settled.
"""
from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, Header, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from adapter import PaystackAmbiguousError, PaystackClient
from api.deps import get_paystack
from db import get_session
from webhook.handler import InvalidSignatureError, handle_webhook

log = logging.getLogger("api.webhooks")
router = APIRouter(prefix="/webhooks", tags=["webhooks"])


@router.post("/paystack")
async def paystack_webhook(
    request: Request,
    session: AsyncSession = Depends(get_session),
    paystack: PaystackClient = Depends(get_paystack),
    x_paystack_signature: str | None = Header(default=None, alias="x-paystack-signature"),
):
    raw_body = await request.body()
    try:
        result = await handle_webhook(
            session, paystack, raw_body=raw_body, signature=x_paystack_signature
        )
    except InvalidSignatureError:
        raise HTTPException(status_code=401, detail="invalid signature")
    except PaystackAmbiguousError:
        # Could not confirm with Paystack right now. Ask for redelivery; do not
        # pretend success. The reconciler will also catch this payment.
        raise HTTPException(status_code=503, detail="verification unavailable; retry")
    except Exception:  # noqa: BLE001 - surface as 5xx so Paystack redelivers
        log.exception("webhook processing failed; requesting redelivery")
        raise HTTPException(status_code=500, detail="processing failed; retry")

    return result


# ============================================================
# SOURCE: webhook\handler.py
# ============================================================

"""Paystack webhook processing: verify -> deduplicate -> act.

Ordering and why it is safe:

1. **Verify the signature** on the raw body (HMAC-SHA512). Unsigned/invalid ->
   reject. Authentication happens before we touch the database.

2. **Deduplicate** on ``event_id`` (UNIQUE). Paystack has no native delivery
   UUID, so we derive a stable one from ``<event>:<data.id>``. A redelivery of
   the same charge collides and is ignored.

   The subtlety: we only *short-circuit* on a duplicate that was already
   ``processed_at``-stamped. A row that exists but was never finished (a prior
   attempt crashed mid-processing) is allowed through again, because Paystack
   keeps retrying and we want that retry to actually complete. The real
   double-effect protection lives in ``complete_payment`` (row lock + state
   machine + UNIQUE enrollment), so reprocessing is harmless regardless.

3. **Act** only on ``charge.success``, via the shared idempotent
   ``complete_payment``. If it raises (ambiguous Paystack verify, DB error) we
   let it propagate: the endpoint returns 5xx, Paystack redelivers later, and
   ``processed_at`` stays NULL so the retry is not deduped away. The reconciler
   is the second safety net.

The transactions below are deliberately short and non-overlapping so they never
nest with the transaction ``complete_payment`` opens on the same session.
"""
from __future__ import annotations

import json
import logging
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from adapter import PaystackClient
from models import WebhookEvent
from services.payments import complete_payment

log = logging.getLogger("webhook")


class InvalidSignatureError(Exception):
    pass


def _derive_event_id(event_type: str, data: dict) -> str:
    """Stable id for one logical event. ``data.id`` is Paystack's transaction
    id; falling back to reference keeps us deduplicating even if it's absent."""
    ident = data.get("id") or data.get("reference") or "unknown"
    return f"{event_type}:{ident}"


async def _event_status(session: AsyncSession, event_id: str) -> tuple[bool, bool]:
    """Return ``(exists, processed)`` for ``event_id`` and close the read
    transaction.

    We select the *column value* rather than the ORM row on purpose: the
    ``rollback`` below expires any loaded instance, and a subsequent attribute
    access would trigger an implicit lazy-load — illegal under async SQLAlchemy
    (``MissingGreenlet``). Returning plain scalars keeps the caller safe.
    """
    row = (
        await session.execute(
            select(WebhookEvent.processed_at).where(
                WebhookEvent.event_id == event_id
            )
        )
    ).first()
    await session.rollback()  # close the read transaction
    if row is None:
        return (False, False)
    return (True, row[0] is not None)


async def handle_webhook(
    session: AsyncSession,
    paystack: PaystackClient,
    *,
    raw_body: bytes,
    signature: str | None,
) -> dict:
    if not paystack.verify_signature(raw_body, signature):
        raise InvalidSignatureError("invalid or missing x-paystack-signature")

    event = json.loads(raw_body.decode("utf-8"))
    event_type = event.get("event", "unknown")
    data = event.get("data", {}) or {}
    event_id = _derive_event_id(event_type, data)
    reference = data.get("reference")

    # --- dedup: fast-path only fully-processed duplicates ----------------
    exists, processed = await _event_status(session, event_id)
    if exists and processed:
        log.info("duplicate webhook %s already processed; ignoring", event_id)
        return {"status": "duplicate", "event_id": event_id}

    # Record the event if new (UNIQUE(event_id) guards a concurrent delivery).
    if not exists:
        session.add(
            WebhookEvent(
                event_id=event_id,
                event_type=event_type,
                reference=reference,
                payload=event,
            )
        )
        try:
            await session.commit()
        except IntegrityError:
            await session.rollback()  # concurrent delivery won the insert; fine

    # --- act (idempotent; opens its own transaction) ---------------------
    # Only charge.success grants access. Other events are recorded for audit and
    # acknowledged so Paystack stops retrying them. If this raises, we do NOT
    # stamp processed_at below (we never reach it) -> redelivery may retry.
    if event_type == "charge.success" and reference:
        await complete_payment(
            session, paystack, reference=reference, source="webhook"
        )

    # --- stamp processed only after the side effect succeeded ------------
    async with session.begin():
        record = await session.scalar(
            select(WebhookEvent).where(WebhookEvent.event_id == event_id)
        )
        if record is not None:
            record.processed_at = datetime.now(timezone.utc)

    return {"status": "processed", "event_id": event_id}


# ============================================================
# SOURCE: jobs\reconcile.py
# ============================================================

"""Reconciliation worker - the recovery path for every ambiguous outcome.

Why it exists: a webhook can be lost, the server can crash after Paystack
charged the card but before we recorded completion, or an ``initialize`` can
time out with the transaction actually created. In all of these the payment is
left ``pending``. This job is the sweep that drives every pending payment to a
terminal state by asking Paystack what really happened - the single source of
truth.

It is deliberately built out of the same idempotent ``complete_payment`` used
by the webhook, so running it repeatedly, or concurrently with a late webhook,
can never double-charge or double-enroll.

Run it as its own process:

    python -m jobs.reconcile            # one pass
    python -m jobs.reconcile --loop     # forever, every RECONCILE_INTERVAL

(In production run it as a separate worker / cron, not inside the API.)
"""
from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from adapter import PaystackAmbiguousError, PaystackClient, PaystackDefiniteError
from config import Settings, get_settings
from models import Payment, PaymentStatus
from services.payments import complete_payment

log = logging.getLogger("reconcile")


async def reconcile_once(
    session: AsyncSession,
    paystack: PaystackClient,
    settings: Settings,
    *,
    now: datetime | None = None,
) -> dict:
    """Process one batch of stale pending payments. Returns a small summary
    dict (handy for tests and metrics)."""
    now = now or datetime.now(timezone.utc)
    cutoff = now - timedelta(seconds=settings.reconcile_min_age_seconds)
    abandon_before = now - timedelta(seconds=settings.reconcile_abandon_after_seconds)

    # Only touch payments old enough that the webhook/callback has had its
    # chance - otherwise we race them for no reason.
    stale = (
        await session.scalars(
            select(Payment)
            .where(Payment.status == PaymentStatus.pending)
            .where(Payment.created_at <= cutoff)
            .order_by(Payment.created_at)
            .limit(settings.reconcile_batch_size)
        )
    ).all()
    # Close the read transaction before the loop: complete_payment() opens its
    # own transaction per payment, and they must not nest on this session.
    await session.commit()

    summary = {"scanned": len(stale), "completed": 0, "failed": 0, "ambiguous": 0}

    for payment in stale:
        reference = payment.reference
        try:
            result = await complete_payment(
                session, paystack, reference=reference, source="reconcile"
            )
            if result is not None and result.status is PaymentStatus.completed:
                summary["completed"] += 1
            elif result is not None and result.status is PaymentStatus.failed:
                summary["failed"] += 1
        except PaystackAmbiguousError:
            # Still unknown - leave pending and try again next run. Never guess.
            summary["ambiguous"] += 1
            log.info("reference=%s still ambiguous; will retry", reference)
        except PaystackDefiniteError as exc:
            # Paystack has no/failed record. If the payment is old enough that a
            # success is implausible, abandon it so the course frees up.
            if payment.created_at and _as_aware(payment.created_at) <= abandon_before:
                await _mark_failed(session, reference)
                summary["failed"] += 1
                log.info("reference=%s abandoned (definite error, aged out): %s",
                         reference, exc)
            else:
                log.info("reference=%s definite error but still young; leaving: %s",
                         reference, exc)
        except Exception:  # noqa: BLE001 - one bad row must not stop the sweep
            log.exception("reconcile failed for reference=%s", reference)

    return summary


def _as_aware(dt: datetime) -> datetime:
    return dt if dt.tzinfo is not None else dt.replace(tzinfo=timezone.utc)


async def _mark_failed(session: AsyncSession, reference: str) -> None:
    async with session.begin():
        payment = await session.scalar(
            select(Payment).where(Payment.reference == reference).with_for_update()
        )
        if payment is not None and payment.status is PaymentStatus.pending:
            payment.status = PaymentStatus.failed


async def run_forever(
    session_factory: async_sessionmaker[AsyncSession],
    paystack: PaystackClient,
    settings: Settings,
) -> None:
    log.info("reconciliation loop started (every %ss)",
             settings.reconcile_interval_seconds)
    while True:
        try:
            async with session_factory() as session:
                summary = await reconcile_once(session, paystack, settings)
            if summary["scanned"]:
                log.info("reconcile pass: %s", summary)
        except asyncio.CancelledError:
            log.info("reconciliation loop stopping")
            raise
        except Exception:  # noqa: BLE001 - never let the loop die
            log.exception("reconcile pass crashed; continuing")
        await asyncio.sleep(settings.reconcile_interval_seconds)


async def _main(loop: bool) -> None:
    import httpx

    from db import SessionLocal

    settings = get_settings()
    async with httpx.AsyncClient(
        timeout=httpx.Timeout(settings.paystack_timeout_seconds)
    ) as http:
        paystack = PaystackClient(settings=settings, client=http)
        if loop:
            await run_forever(SessionLocal, paystack, settings)
        else:
            async with SessionLocal() as session:
                summary = await reconcile_once(session, paystack, settings)
            log.info("reconcile pass: %s", summary)


if __name__ == "__main__":  # pragma: no cover
    import sys

    logging.basicConfig(level=logging.INFO)
    asyncio.run(_main(loop="--loop" in sys.argv))


# ============================================================
# SOURCE: tests\conftest.py
# ============================================================

"""Shared test fixtures.

IMPORTANT ordering note
-----------------------
``db.py`` builds the SQLAlchemy engine at *import time* from ``DATABASE_URL``,
and ``config.get_settings`` is ``lru_cache``-d. So we must set a SQLite
``DATABASE_URL`` (and dummy Paystack settings) and clear the settings cache
*before* importing anything from the project. That happens at the very top of
this module, which pytest imports before collecting any test.

The suite runs entirely against SQLite (``aiosqlite``) using a fresh temp-file
database per test, so multiple sessions get genuinely separate connections -
this is what lets the concurrency tests exercise the UNIQUE-constraint race
paths. SQLite silently ignores ``SELECT ... FOR UPDATE``; the invariants under
test (I1/I2) are additionally guarded by UNIQUE constraints + the state
machine, which is what these tests assert against.
"""
from __future__ import annotations

import hashlib
import hmac
import json
import os
import tempfile
from datetime import datetime, timezone

# --- env must be set BEFORE importing project modules ----------------------
TEST_SECRET = "sk_test_fake_secret_key"
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///:memory:"  # module engine; unused by tests
os.environ["PAYSTACK_SECRET_KEY"] = TEST_SECRET
os.environ["PAYSTACK_PUBLIC_KEY"] = "pk_test_fake"
os.environ["PUBLIC_BASE_URL"] = "http://test"
os.environ["RUN_RECONCILE_IN_PROCESS"] = "false"

import httpx  # noqa: E402
import pytest  # noqa: E402
import pytest_asyncio  # noqa: E402
from sqlalchemy.ext.asyncio import (  # noqa: E402
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from config import get_settings  # noqa: E402

get_settings.cache_clear()  # drop any cache populated during import

from adapter import (  # noqa: E402
    PaystackAmbiguousError,
    VerificationResult,
)
from db import Base  # noqa: E402
from models import Course, Payment, PaymentStatus  # noqa: E402
from models._ids import new_uuid  # noqa: E402


# ---------------------------------------------------------------------------
# Paystack test double
# ---------------------------------------------------------------------------
class FakePaystack:
    """In-memory stand-in for ``PaystackClient``.

    ``verify_transaction`` is the source of truth the code re-checks, so tests
    drive enrollment outcomes by configuring it per-reference. Records every
    call so tests can assert *how often* the network was touched (e.g. that a
    duplicate webhook does NOT re-verify)."""

    def __init__(self, secret_key: str = TEST_SECRET) -> None:
        self.secret_key = secret_key
        self._verify: dict[str, object] = {}
        self._default_verify: object | None = None
        self.verify_calls: list[str] = []
        self.init_calls: list[dict] = []
        # None -> behave normally; otherwise an Exception (instance or class)
        # to raise from initialize_transaction.
        self.init_behavior: object | None = None

    # -- configuration helpers --------------------------------------------
    def set_verify(self, reference: str, result: object) -> None:
        self._verify[reference] = result

    def set_default_verify(self, result: object) -> None:
        self._default_verify = result

    # -- interface used by the code ---------------------------------------
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
        self.init_calls.append(
            {"reference": reference, "idempotency_key": idempotency_key,
             "amount": amount, "email": email}
        )
        _maybe_raise(self.init_behavior)
        return {
            "authorization_url": f"https://checkout.test/{reference}",
            "access_code": f"acc_{reference}",
            "reference": reference,
        }

    async def verify_transaction(self, reference: str) -> VerificationResult:
        self.verify_calls.append(reference)
        result = self._verify.get(reference, self._default_verify)
        if result is None:
            raise AssertionError(
                f"test did not configure a verify result for reference={reference!r}"
            )
        _maybe_raise(result)
        return result  # type: ignore[return-value]

    def verify_signature(self, raw_body: bytes, signature: str | None) -> bool:
        if not signature:
            return False
        computed = hmac.new(
            self.secret_key.encode("utf-8"), raw_body, hashlib.sha512
        ).hexdigest()
        return hmac.compare_digest(computed, signature)

    # -- test convenience --------------------------------------------------
    def sign(self, raw_body: bytes) -> str:
        return hmac.new(
            self.secret_key.encode("utf-8"), raw_body, hashlib.sha512
        ).hexdigest()


def _maybe_raise(x: object) -> None:
    if isinstance(x, BaseException):
        raise x
    if isinstance(x, type) and issubclass(x, BaseException):
        raise x("injected failure")


# ---------------------------------------------------------------------------
# Database fixtures (fresh temp-file SQLite per test)
# ---------------------------------------------------------------------------
@pytest_asyncio.fixture
async def engine():
    fd, path = tempfile.mkstemp(suffix=".sqlite")
    os.close(fd)
    url = "sqlite+aiosqlite:///" + path.replace(os.sep, "/")
    eng = create_async_engine(url, connect_args={"timeout": 30})
    async with eng.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    try:
        yield eng
    finally:
        await eng.dispose()
        try:
            os.unlink(path)
        except OSError:
            pass


@pytest.fixture
def session_factory(engine) -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


@pytest_asyncio.fixture
async def session(session_factory) -> AsyncSession:
    async with session_factory() as s:
        yield s


@pytest_asyncio.fixture
async def course(session_factory) -> Course:
    async with session_factory() as s:
        c = Course(title="Distributed Systems 101", price=500000, currency="NGN")
        s.add(c)
        await s.commit()
        await s.refresh(c)
        _ = (c.id, c.price, c.currency)  # load before detach
        return c


# ---------------------------------------------------------------------------
# Paystack + HTTP client fixtures
# ---------------------------------------------------------------------------
@pytest.fixture
def fake_paystack() -> FakePaystack:
    return FakePaystack()


@pytest_asyncio.fixture
async def client(session_factory, fake_paystack):
    """httpx client bound to the FastAPI app with DB + Paystack overridden.

    Lifespan is intentionally NOT run (ASGITransport skips it), and both
    external dependencies are overridden, so the app talks to the per-test
    SQLite DB and the fake Paystack instead of the module-level engine / real
    provider."""
    from api.deps import get_paystack
    from db import get_session
    from main import app

    async def _get_session():
        async with session_factory() as s:
            yield s

    app.dependency_overrides[get_session] = _get_session
    app.dependency_overrides[get_paystack] = lambda: fake_paystack
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as c:
        yield c
    app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# Builders (returned as callables so tests stay declarative)
# ---------------------------------------------------------------------------
@pytest.fixture
def vr():
    def _vr(
        reference: str,
        *,
        status: str = "success",
        amount: int = 500000,
        currency: str = "NGN",
        txn_id: str | None = "txn_1",
    ) -> VerificationResult:
        return VerificationResult(
            reference=reference,
            status=status,
            amount=amount,
            currency=currency,
            transaction_id=txn_id,
            raw={"reference": reference, "status": status, "amount": amount,
                 "currency": currency, "id": txn_id},
        )

    return _vr


@pytest.fixture
def charge_success_body():
    def _body(
        reference: str,
        *,
        amount: int = 500000,
        currency: str = "NGN",
        txn_id: int = 424242,
        event: str = "charge.success",
        status: str = "success",
    ) -> bytes:
        return json.dumps(
            {
                "event": event,
                "data": {
                    "id": txn_id,
                    "reference": reference,
                    "status": status,
                    "amount": amount,
                    "currency": currency,
                },
            }
        ).encode("utf-8")

    return _body


@pytest.fixture
def make_pending(session_factory):
    """Create a durable ``pending`` payment directly, simulating the state left
    behind after ``initialize`` (and, in the crash tests, after Paystack has
    actually charged but before we recorded completion)."""

    async def _make(
        course: Course,
        *,
        student_id: int = 1,
        email: str = "student@test.io",
        idempotency_key: str | None = None,
        reference: str | None = None,
        status: PaymentStatus = PaymentStatus.pending,
        created_at: datetime | None = None,
    ) -> Payment:
        async with session_factory() as s:
            p = Payment(
                reference=reference or new_uuid(),
                idempotency_key=idempotency_key or f"key_{new_uuid()}",
                student_id=student_id,
                course_id=course.id,
                amount=course.price,
                currency=course.currency,
                email=email,
                status=status,
            )
            if created_at is not None:
                p.created_at = created_at
            s.add(p)
            await s.commit()
            await s.refresh(p)
            _ = (p.id, p.reference, p.idempotency_key, p.status, p.amount)
            return p

    return _make


@pytest.fixture
def make_settings():
    """Return a copy of the settings with overrides (e.g. tiny reconcile
    windows) without mutating the cached singleton."""

    def _make(**overrides):
        return get_settings().model_copy(update=overrides)

    return _make


# Re-export a couple of names tests reach for.
UTC = timezone.utc
__all__ = ["FakePaystack", "PaystackAmbiguousError", "UTC"]


# ============================================================
# SOURCE: tests\test_initialize_payment.py
# ============================================================

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


# ============================================================
# SOURCE: tests\test_complete_payment.py
# ============================================================

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


# ============================================================
# SOURCE: tests\test_webhook.py
# ============================================================

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


# ============================================================
# SOURCE: tests\test_reconcile.py
# ============================================================

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


# ============================================================
# SOURCE: tests\test_invariants.py
# ============================================================

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
