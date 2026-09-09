"""Shared test fixtures.

Tests run the ASGI app in-process against an in-memory SQLite database and a
fake Paystack client (no network). The Paystack *signature* check is NOT faked —
webhook tests compute a real HMAC-SHA512 with the test secret so the real
verification code path is exercised.

The engine is created per-test so it is bound to the active event loop (avoids
pytest-asyncio "future attached to a different loop" issues) and each test gets
a pristine database.
"""
import hashlib
import hmac
import os

# Must be set before importing app modules (config reads the environment).
os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite://")
os.environ.setdefault("PAYSTACK_SECRET_KEY", "sk_test_dummy_secret_key")
os.environ.setdefault("PAYSTACK_BASE_URL", "https://api.paystack.co")
os.environ.setdefault("JWT_SECRET_KEY", "test-jwt-secret-key-at-least-32-bytes-long-for-hs256")
os.environ.setdefault("DEFAULT_CURRENCY", "NGN")

from decimal import Decimal  # noqa: E402

import pytest  # noqa: E402
import pytest_asyncio  # noqa: E402
from httpx import ASGITransport, AsyncClient  # noqa: E402
from sqlalchemy import select  # noqa: E402
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine  # noqa: E402
from sqlalchemy.pool import StaticPool  # noqa: E402

from app.config import settings  # noqa: E402
from app.database import Base, get_session  # noqa: E402
from app.main import app  # noqa: E402
from app.models import Course, User  # noqa: E402
from app.services.paystack import PaystackError, get_paystack  # noqa: E402


class FakePaystack:
    """Stand-in for PaystackClient. Records the amount seen at initialize and
    echoes it back at verify, so the happy path matches by default. Tests can
    force failure modes via the override knobs."""

    def __init__(self) -> None:
        self.amounts: dict[str, int] = {}
        self.verify_status = "success"
        self.verify_currency = "NGN"
        self.amount_override: int | None = None  # force a wrong verified amount
        self.fail_initialize = False

    async def initialize_transaction(
        self, *, email, amount_kobo, reference, callback_url=None, metadata=None
    ):
        if self.fail_initialize:
            raise PaystackError("simulated initialize failure")
        self.amounts[reference] = amount_kobo
        return {
            "authorization_url": f"https://checkout.paystack.com/{reference}",
            "access_code": f"acc_{reference}",
            "reference": reference,
        }

    async def verify_transaction(self, reference):
        amount = (
            self.amount_override
            if self.amount_override is not None
            else self.amounts.get(reference, 0)
        )
        return {
            "status": self.verify_status,
            "reference": reference,
            "amount": amount,
            "currency": self.verify_currency,
            "paid_at": "2026-08-24T12:00:00Z",
        }


@pytest.fixture
def fake_paystack() -> FakePaystack:
    return FakePaystack()


@pytest_asyncio.fixture
async def db_session_factory():
    engine = create_async_engine(
        "sqlite+aiosqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    factory = async_sessionmaker(engine, expire_on_commit=False, autoflush=False)
    try:
        yield factory
    finally:
        await engine.dispose()


@pytest_asyncio.fixture
async def client(db_session_factory, fake_paystack):
    async def _override_get_session():
        async with db_session_factory() as session:
            yield session

    app.dependency_overrides[get_session] = _override_get_session
    app.dependency_overrides[get_paystack] = lambda: fake_paystack
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def course(db_session_factory) -> Course:
    async with db_session_factory() as session:
        c = Course(
            title="Test Course",
            slug="test-course",
            description="A course for tests",
            price=Decimal("5000.00"),
            currency="NGN",
            content="THE SECRET COURSE MATERIAL",
            is_published=True,
        )
        session.add(c)
        await session.commit()
        await session.refresh(c)
        return c


@pytest.fixture
def make_auth_headers(client):
    async def _make(email="student@test.com", password="password123", full_name="Student"):
        await client.post(
            "/auth/register",
            json={"email": email, "password": password, "full_name": full_name},
        )
        resp = await client.post(
            "/auth/login", data={"username": email, "password": password}
        )
        assert resp.status_code == 200, resp.text
        return {"Authorization": f"Bearer {resp.json()['access_token']}"}

    return _make


@pytest.fixture
def make_admin_headers(client, db_session_factory):
    async def _make(email="admin@test.com", password="password123"):
        await client.post(
            "/auth/register",
            json={"email": email, "password": password, "full_name": "Admin"},
        )
        async with db_session_factory() as session:
            user = await session.scalar(select(User).where(User.email == email))
            user.is_admin = True
            await session.commit()
        resp = await client.post(
            "/auth/login", data={"username": email, "password": password}
        )
        assert resp.status_code == 200, resp.text
        return {"Authorization": f"Bearer {resp.json()['access_token']}"}

    return _make


@pytest.fixture
def sign_webhook():
    def _sign(raw: bytes) -> str:
        return hmac.new(
            settings.PAYSTACK_SECRET_KEY.encode(), raw, hashlib.sha512
        ).hexdigest()

    return _sign
