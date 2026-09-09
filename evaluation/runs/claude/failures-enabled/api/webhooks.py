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
