"""
Limited course-seat inventory (PostgreSQL).

Failures review_plan / review_code / check_invariant applied before finalize.

- Decrement seats only when remaining_seats > 0 (row lock + version CAS)
- Unique (student, course) + idempotency_key UNIQUE; cached duplicate response
- TokenBucket on mutating POST; operation_id / request_id in logs
"""

from __future__ import annotations

import json
import logging
import os
import time
import uuid
from datetime import datetime, timezone

from fastapi import Depends, FastAPI, Header, HTTPException, Request
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import (
    CheckConstraint,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    create_engine,
    text,
)
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, declarative_base, sessionmaker

DATABASE_URL = os.getenv(
    "DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/inventory"
)

engine = create_engine(
    DATABASE_URL, pool_size=20, max_overflow=10, pool_timeout=5, pool_pre_ping=True
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()
app = FastAPI(title="Course seats")
logger = logging.getLogger("inventory")


class TokenBucket:
    """Per-key token bucket rate limiter."""

    def __init__(self, rate: float = 8.0, capacity: float = 16.0):
        self.rate = rate
        self.capacity = capacity
        self.tokens: dict[str, float] = {}
        self.updated: dict[str, float] = {}

    def rate_limit(self, key: str) -> bool:
        now = time.monotonic()
        tokens = self.tokens.get(key, self.capacity)
        last = self.updated.get(key, now)
        tokens = min(self.capacity, tokens + (now - last) * self.rate)
        self.updated[key] = now
        if tokens < 1:
            self.tokens[key] = tokens
            return False
        self.tokens[key] = tokens - 1
        return True


limiter = TokenBucket()


class Course(Base):
    __tablename__ = "courses"
    __table_args__ = (
        CheckConstraint("remaining_seats >= 0", name="ck_remaining_seats_nonnegative"),
    )

    id = Column(Integer, primary_key=True)
    title = Column(String, nullable=False)
    capacity = Column(Integer, nullable=False)
    remaining_seats = Column(Integer, nullable=False)
    version = Column(Integer, nullable=False, default=0)


class Student(Base):
    __tablename__ = "students"

    id = Column(Integer, primary_key=True)
    email = Column(String, unique=True, nullable=False)


class SeatHold(Base):
    """One seat reservation per student+course; retries reuse idempotency_key."""

    __tablename__ = "seat_holds"
    __table_args__ = (
        UniqueConstraint("student_id", "course_id", name="uq_hold_student_course"),
        UniqueConstraint("idempotency_key", name="uq_hold_idempotency_key"),
    )

    id = Column(Integer, primary_key=True)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False)
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=False)
    idempotency_key = Column(String, nullable=False)
    cached_response = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class CourseCreate(BaseModel):
    title: str
    capacity: int = Field(ge=0)


class ReserveRequest(BaseModel):
    email: EmailStr
    idempotency_key: str = Field(min_length=8)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def operation_id_from(x_request_id: str) -> str:
    return x_request_id or str(uuid.uuid4())


@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)


@app.post("/courses", status_code=201)
def create_course(
    payload: CourseCreate,
    request: Request,
    db: Session = Depends(get_db),
    x_request_id: str = Header(default=""),
):
    operation_id = operation_id_from(x_request_id)
    ip = request.client.host if request.client else "unknown"
    if not limiter.rate_limit(ip):
        raise HTTPException(status_code=429, detail="Too many requests")
    course = Course(
        title=payload.title,
        capacity=payload.capacity,
        remaining_seats=payload.capacity,
        version=0,
    )
    db.add(course)
    db.commit()
    db.refresh(course)
    logger.info(
        "course created operation_id=%s request_id=%s course_id=%s",
        operation_id,
        operation_id,
        course.id,
    )
    return {
        "id": course.id,
        "title": course.title,
        "capacity": course.capacity,
        "remaining_seats": course.remaining_seats,
        "operation_id": operation_id,
    }


@app.post("/courses/{course_id}/holds", status_code=201)
def reserve_seat(
    course_id: int,
    payload: ReserveRequest,
    request: Request,
    db: Session = Depends(get_db),
    x_request_id: str = Header(default=""),
):
    operation_id = operation_id_from(x_request_id)
    ip = request.client.host if request.client else "unknown"
    if not limiter.rate_limit(ip):
        logger.info("reserve rate_limit operation_id=%s request_id=%s", operation_id, operation_id)
        raise HTTPException(status_code=429, detail="Too many requests")

    existing_key = (
        db.query(SeatHold).filter(SeatHold.idempotency_key == payload.idempotency_key).first()
    )
    if existing_key:
        logger.info(
            "reserve cached operation_id=%s request_id=%s key=%s",
            operation_id,
            operation_id,
            payload.idempotency_key,
        )
        body = (
            json.loads(existing_key.cached_response)
            if existing_key.cached_response
            else {"hold_id": existing_key.id, "dedup": True}
        )
        body["dedup"] = True
        return body

    email = payload.email.lower()
    student = db.query(Student).filter(Student.email == email).first()
    if not student:
        student = Student(email=email)
        db.add(student)
        try:
            db.flush()
        except IntegrityError:
            db.rollback()
            student = db.query(Student).filter(Student.email == email).first()
            if not student:
                raise HTTPException(status_code=409, detail="Student conflict")

    already = (
        db.query(SeatHold)
        .filter(SeatHold.student_id == student.id, SeatHold.course_id == course_id)
        .first()
    )
    if already:
        body = (
            json.loads(already.cached_response)
            if already.cached_response
            else {"hold_id": already.id, "course_id": course_id, "status": "already_held"}
        )
        body["dedup"] = True
        logger.info(
            "reserve already-held operation_id=%s request_id=%s student_id=%s",
            operation_id,
            operation_id,
            student.id,
        )
        return body

    # Lock + atomic decrement in the same transaction (no lost update, no negative seats).
    row = (
        db.execute(
            text(
                "SELECT id, remaining_seats, version FROM courses WHERE id = :id FOR UPDATE"
            ),
            {"id": course_id},
        )
        .mappings()
        .first()
    )
    if not row:
        db.rollback()
        raise HTTPException(status_code=404, detail="Course not found")

    result = db.execute(
        text(
            "UPDATE courses SET remaining_seats = remaining_seats - 1, version = version + 1 "
            "WHERE id = :id AND remaining_seats > 0 AND version = :version"
        ),
        {"id": course_id, "version": row["version"]},
    )
    if result.rowcount != 1:
        db.rollback()
        logger.info(
            "reserve conflict operation_id=%s request_id=%s course_id=%s",
            operation_id,
            operation_id,
            course_id,
        )
        raise HTTPException(status_code=409, detail="Course is full or concurrent conflict")

    remaining = row["remaining_seats"] - 1
    hold = SeatHold(
        student_id=student.id,
        course_id=course_id,
        idempotency_key=payload.idempotency_key,
    )
    db.add(hold)
    try:
        db.flush()
    except IntegrityError:
        db.rollback()
        raced = (
            db.query(SeatHold)
            .filter(SeatHold.idempotency_key == payload.idempotency_key)
            .first()
        )
        if raced:
            body = json.loads(raced.cached_response) if raced.cached_response else {
                "hold_id": raced.id,
                "dedup": True,
            }
            body["dedup"] = True
            return body
        raise HTTPException(status_code=409, detail="Duplicate reservation")

    payload_out = {
        "hold_id": hold.id,
        "course_id": course_id,
        "student_id": student.id,
        "remaining_seats": remaining,
        "status": "held",
        "operation_id": operation_id,
        "dedup": False,
    }
    hold.cached_response = json.dumps(payload_out)
    db.commit()
    logger.info(
        "reserve success operation_id=%s request_id=%s hold_id=%s remaining=%s",
        operation_id,
        operation_id,
        hold.id,
        remaining,
    )
    return payload_out


@app.get("/courses/{course_id}")
def get_course(course_id: int, db: Session = Depends(get_db)):
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    return {
        "id": course.id,
        "title": course.title,
        "capacity": course.capacity,
        "remaining_seats": course.remaining_seats,
        "version": course.version,
    }
