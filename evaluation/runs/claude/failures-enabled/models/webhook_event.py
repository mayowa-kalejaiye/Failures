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
