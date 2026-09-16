"""
Authentication with login and JWT refresh (PostgreSQL).

Failures review_plan / review_code / check_invariant applied before finalize.

- TokenBucket rate limit + lockout on /login (brute-force throttle)
- SELECT ... FOR UPDATE + version column on refresh (no lost update)
- Token rotate CAS: UPDATE ... WHERE version = :version AND refresh_token = :old
- operation_id / request_id in structured logs
- Connection pool for concurrent logins
"""

from __future__ import annotations

import logging
import os
import time
import uuid
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from typing import Optional

import jwt
from fastapi import Depends, FastAPI, Header, HTTPException, Request
from passlib.context import CryptContext
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import (
    Column,
    DateTime,
    Integer,
    String,
    create_engine,
    text,
)
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, declarative_base, sessionmaker

DATABASE_URL = os.getenv(
    "DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/auth"
)
JWT_SECRET = os.getenv("JWT_SECRET", "dev-secret-change-me")
JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_MINUTES = 15
REFRESH_TOKEN_DAYS = 7
LOGIN_FAILURES_BEFORE_LOCKOUT = 5
LOCKOUT_SECONDS = 300

engine = create_engine(
    DATABASE_URL,
    pool_size=20,
    max_overflow=10,
    pool_timeout=5,
    pool_pre_ping=True,
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
app = FastAPI(title="Auth")
logger = logging.getLogger("auth")


class TokenBucket:
    """Per-key token bucket rate limiter (burst + average rate)."""

    def __init__(self, rate: float = 5.0, capacity: float = 5.0):
        self.rate = rate
        self.capacity = capacity
        self.tokens: dict[str, float] = defaultdict(lambda: capacity)
        self.updated: dict[str, float] = defaultdict(time.monotonic)

    def rate_limit(self, key: str) -> bool:
        now = time.monotonic()
        elapsed = now - self.updated[key]
        self.tokens[key] = min(self.capacity, self.tokens[key] + elapsed * self.rate)
        self.updated[key] = now
        if self.tokens[key] < 1:
            return False
        self.tokens[key] -= 1
        return True


limiter = TokenBucket(rate=3.0, capacity=5.0)
_failures: dict[str, int] = defaultdict(int)
_lockout_until: dict[str, float] = {}


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    refresh_token = Column(String, nullable=True)
    version = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class RefreshRequest(BaseModel):
    refresh_token: str


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def create_access_token(user_id: int, operation_id: str) -> str:
    payload = {
        "sub": str(user_id),
        "type": "access",
        "operation_id": operation_id,
        "exp": utcnow() + timedelta(minutes=ACCESS_TOKEN_MINUTES),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def create_refresh_token(user_id: int, operation_id: str) -> str:
    payload = {
        "sub": str(user_id),
        "type": "refresh",
        "operation_id": operation_id,
        "exp": utcnow() + timedelta(days=REFRESH_TOKEN_DAYS),
        "jti": str(uuid.uuid4()),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def client_key(request: Request, email: str = "") -> str:
    ip = request.client.host if request.client else "unknown"
    return f"{ip}:{email.lower()}" if email else ip


def operation_id_from(x_request_id: str) -> str:
    return x_request_id or str(uuid.uuid4())


@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)


@app.post("/register", status_code=201)
def register(
    payload: RegisterRequest,
    db: Session = Depends(get_db),
    x_request_id: str = Header(default=""),
):
    operation_id = operation_id_from(x_request_id)
    user = User(
        email=payload.email.lower(),
        hashed_password=pwd_context.hash(payload.password),
        version=0,
    )
    db.add(user)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        logger.info(
            "register conflict operation_id=%s request_id=%s email=%s",
            operation_id,
            operation_id,
            payload.email,
        )
        raise HTTPException(status_code=409, detail="Email already registered")
    db.refresh(user)
    logger.info(
        "user registered operation_id=%s request_id=%s user_id=%s",
        operation_id,
        operation_id,
        user.id,
    )
    return {"id": user.id, "email": user.email, "operation_id": operation_id}


@app.post("/login")
def login(
    payload: LoginRequest,
    request: Request,
    db: Session = Depends(get_db),
    x_request_id: str = Header(default=""),
):
    operation_id = operation_id_from(x_request_id)
    key = client_key(request, payload.email)

    if _lockout_until.get(key, 0) > time.monotonic():
        logger.info("login lockout operation_id=%s request_id=%s key=%s", operation_id, operation_id, key)
        raise HTTPException(status_code=429, detail="Account temporarily locked")

    if not limiter.rate_limit(key):
        logger.info("login rate_limit operation_id=%s request_id=%s key=%s", operation_id, operation_id, key)
        raise HTTPException(status_code=429, detail="Too many login attempts")

    email = payload.email.lower()
    user = db.query(User).filter(User.email == email).first()
    if not user or not pwd_context.verify(payload.password, user.hashed_password):
        _failures[key] += 1
        if _failures[key] >= LOGIN_FAILURES_BEFORE_LOCKOUT:
            _lockout_until[key] = time.monotonic() + LOCKOUT_SECONDS
            logger.info(
                "login lockout armed operation_id=%s request_id=%s key=%s",
                operation_id,
                operation_id,
                key,
            )
        raise HTTPException(status_code=401, detail="Invalid credentials")

    _failures[key] = 0
    access = create_access_token(user.id, operation_id)
    refresh = create_refresh_token(user.id, operation_id)

    # Same transaction: lock row then CAS version so concurrent logins serialize.
    db.execute(
        text("SELECT id, version FROM users WHERE id = :id FOR UPDATE"),
        {"id": user.id},
    )
    result = db.execute(
        text(
            "UPDATE users SET refresh_token = :token, version = version + 1 "
            "WHERE id = :id AND version = :version"
        ),
        {"token": refresh, "id": user.id, "version": user.version},
    )
    if result.rowcount != 1:
        db.rollback()
        logger.info(
            "login version conflict operation_id=%s request_id=%s user_id=%s",
            operation_id,
            operation_id,
            user.id,
        )
        raise HTTPException(status_code=409, detail="Concurrent login conflict")
    db.commit()
    logger.info(
        "login success operation_id=%s request_id=%s user_id=%s",
        operation_id,
        operation_id,
        user.id,
    )
    return {
        "access_token": access,
        "refresh_token": refresh,
        "token_type": "bearer",
        "operation_id": operation_id,
    }


@app.post("/refresh")
def refresh(
    payload: RefreshRequest,
    db: Session = Depends(get_db),
    x_request_id: str = Header(default=""),
):
    operation_id = operation_id_from(x_request_id)
    try:
        decoded = jwt.decode(
            payload.refresh_token, JWT_SECRET, algorithms=[JWT_ALGORITHM]
        )
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    if decoded.get("type") != "refresh":
        raise HTTPException(status_code=401, detail="Invalid token type")

    user_id = int(decoded["sub"])
    # Lock + CAS in one transaction so two concurrent refreshes cannot both win.
    row = (
        db.execute(
            text(
                "SELECT id, refresh_token, version FROM users WHERE id = :id FOR UPDATE"
            ),
            {"id": user_id},
        )
        .mappings()
        .first()
    )
    if not row or row["refresh_token"] != payload.refresh_token:
        db.rollback()
        logger.info(
            "refresh mismatch operation_id=%s request_id=%s user_id=%s",
            operation_id,
            operation_id,
            user_id,
        )
        raise HTTPException(status_code=401, detail="Refresh token mismatch")

    access = create_access_token(user_id, operation_id)
    new_refresh = create_refresh_token(user_id, operation_id)
    result = db.execute(
        text(
            "UPDATE users SET refresh_token = :token, version = version + 1 "
            "WHERE id = :id AND version = :version AND refresh_token = :old"
        ),
        {
            "token": new_refresh,
            "id": user_id,
            "version": row["version"],
            "old": payload.refresh_token,
        },
    )
    if result.rowcount != 1:
        db.rollback()
        logger.info(
            "refresh lost-update prevented operation_id=%s request_id=%s user_id=%s",
            operation_id,
            operation_id,
            user_id,
        )
        raise HTTPException(status_code=409, detail="Concurrent refresh conflict")
    db.commit()
    logger.info(
        "refresh success operation_id=%s request_id=%s user_id=%s",
        operation_id,
        operation_id,
        user_id,
    )
    return {
        "access_token": access,
        "refresh_token": new_refresh,
        "token_type": "bearer",
        "operation_id": operation_id,
    }


@app.get("/me")
def me(
    authorization: Optional[str] = Header(default=None),
    db: Session = Depends(get_db),
    x_request_id: str = Header(default=""),
):
    operation_id = operation_id_from(x_request_id)
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="Missing token")
    token = authorization.split(" ", 1)[1]
    try:
        decoded = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid access token")
    if decoded.get("type") != "access":
        raise HTTPException(status_code=401, detail="Invalid token type")
    user = db.query(User).filter(User.id == int(decoded["sub"])).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    logger.info("me operation_id=%s request_id=%s user_id=%s", operation_id, operation_id, user.id)
    return {"id": user.id, "email": user.email, "operation_id": operation_id}
