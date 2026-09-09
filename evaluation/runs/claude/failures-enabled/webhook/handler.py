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
