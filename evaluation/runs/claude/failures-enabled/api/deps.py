"""FastAPI dependencies."""
from __future__ import annotations

from fastapi import Request

from adapter import PaystackClient


def get_paystack(request: Request) -> PaystackClient:
    """Return the process-wide Paystack client (shares one bounded httpx
    connection pool, created in the app lifespan)."""
    return request.app.state.paystack
