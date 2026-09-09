"""FastAPI application entrypoint."""
from contextlib import asynccontextmanager

from fastapi import FastAPI

from . import models  # noqa: F401  (ensure models are registered on Base.metadata)
from .database import Base, engine
from .routers import auth, courses, enrollments, payments


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Dev-oriented: create tables at startup. Use Alembic for real migrations.
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield


app = FastAPI(
    title="Course Payment & Enrollment API",
    description=(
        "Students pay for courses via Paystack and are automatically enrolled "
        "once payment is verified."
    ),
    version="1.0.0",
    lifespan=lifespan,
)

app.include_router(auth.router)
app.include_router(courses.router)
app.include_router(payments.router)
app.include_router(enrollments.router)


@app.get("/health", tags=["health"])
async def health() -> dict:
    return {"status": "ok"}
