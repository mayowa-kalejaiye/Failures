"""Async SQLAlchemy engine, session factory and declarative base.

The pool is deliberately *bounded* (`pool_size` + `max_overflow`): if Paystack
stalls, requests waiting on it must not open unbounded connections and starve
the database. `pool_pre_ping` recycles connections dropped by the server.
"""
from collections.abc import AsyncIterator

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from config import Settings, get_settings


class Base(DeclarativeBase):
    pass


def build_engine(settings: Settings) -> AsyncEngine:
    """Build an engine. SQLite (used by the tests) does not accept the
    server-style pool arguments, so we only pass them for real databases."""
    url = settings.database_url
    if url.startswith("sqlite"):
        return create_async_engine(url, future=True)
    return create_async_engine(
        url,
        future=True,
        pool_pre_ping=True,
        pool_size=settings.db_pool_size,
        max_overflow=settings.db_max_overflow,
        pool_timeout=settings.db_pool_timeout,
    )


_settings = get_settings()
engine: AsyncEngine = build_engine(_settings)
# expire_on_commit=False: we keep reading model attributes after commit (e.g.
# the freshly persisted `reference`) without triggering a lazy reload.
SessionLocal = async_sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)


async def get_session() -> AsyncIterator[AsyncSession]:
    """FastAPI dependency. The service layer owns its own transaction
    boundaries via `async with session.begin()`, so this only manages the
    connection lifecycle."""
    async with SessionLocal() as session:
        yield session


async def init_models(target: AsyncEngine | None = None) -> None:
    """Create tables. Convenient for the demo / tests; use Alembic migrations
    in production."""
    import models  # noqa: F401  (registers every table on Base.metadata)

    eng = target or engine
    async with eng.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
