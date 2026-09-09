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
