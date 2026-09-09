"""FastAPI application entrypoint.

Wires the routers and owns process-wide resources:

* one bounded ``httpx.AsyncClient`` (connection reuse + a hard timeout on every
  Paystack call), shared via ``app.state.paystack``;
* optional in-process reconciliation loop (demo convenience - prefer a separate
  ``python -m jobs.reconcile`` worker in production).
"""
from __future__ import annotations

import asyncio
import logging
from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI

from adapter import PaystackClient
from api import payments_router, webhooks_router
from config import get_settings
from db import SessionLocal, init_models
from jobs.reconcile import run_forever

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("app")


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()

    # Create tables for the demo. Use Alembic migrations in production.
    await init_models()

    app.state.http = httpx.AsyncClient(
        timeout=httpx.Timeout(settings.paystack_timeout_seconds)
    )
    app.state.paystack = PaystackClient(settings=settings, client=app.state.http)

    reconcile_task: asyncio.Task | None = None
    if settings.run_reconcile_in_process:
        reconcile_task = asyncio.create_task(
            run_forever(SessionLocal, app.state.paystack, settings)
        )
        log.info("in-process reconciliation loop enabled")

    try:
        yield
    finally:
        if reconcile_task is not None:
            reconcile_task.cancel()
            try:
                await reconcile_task
            except asyncio.CancelledError:
                pass
        await app.state.http.aclose()


app = FastAPI(title="Course Payments & Enrollment", lifespan=lifespan)
app.include_router(payments_router)
app.include_router(webhooks_router)


@app.get("/health")
async def health():
    return {"status": "ok"}
