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
