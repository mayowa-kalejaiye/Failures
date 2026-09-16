"""Concurrent-safe limited course seats with FastAPI and PostgreSQL.

This inventory boundary expects an authenticated/authorized caller upstream.  It
does not decide whether a course is paid; it atomically reserves a seat only for
an allowed enrollment request. Set DATABASE_URL to a PostgreSQL SQLAlchemy URL.
"""

from __future__ import annotations

import os
import threading
import time
from datetime import datetime, timezone
from typing import Generator

from fastapi import Depends, FastAPI, HTTPException, Request, status
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Integer, String, UniqueConstraint, create_engine, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, sessionmaker


DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+psycopg://postgres:postgres@localhost/courses")


class Base(DeclarativeBase):
    pass


class Student(Base):
    __tablename__ = "students"
    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(320), unique=True, index=True)


class Course(Base):
    __tablename__ = "courses"
    __table_args__ = (
        CheckConstraint("capacity >= 0", name="ck_course_capacity_nonnegative"),
        CheckConstraint("remaining_seats >= 0", name="ck_course_remaining_nonnegative"),
        CheckConstraint("remaining_seats <= capacity", name="ck_course_remaining_within_capacity"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(200))
    capacity: Mapped[int] = mapped_column(Integer)
    remaining_seats: Mapped[int] = mapped_column(Integer)


class Enrollment(Base):
    __tablename__ = "enrollments"
    __table_args__ = (UniqueConstraint("student_id", "course_id", name="uq_enrollment_student_course"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("students.id"), index=True)
    course_id: Mapped[int] = mapped_column(ForeignKey("courses.id"), index=True)
    enrolled_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


class TokenBucket:
    def __init__(self, capacity: int = 60, refill_per_second: float = 1.0) -> None:
        self.capacity, self.refill_per_second = capacity, refill_per_second
        self.buckets: dict[str, tuple[float, float]] = {}
        self.lock = threading.Lock()

    def consume(self, key: str) -> bool:
        with self.lock:
            now = time.monotonic()
            tokens, updated = self.buckets.get(key, (float(self.capacity), now))
            tokens = min(self.capacity, tokens + (now - updated) * self.refill_per_second)
            self.buckets[key] = (tokens - 1, now) if tokens >= 1 else (tokens, now)
            return tokens >= 1


engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(engine, expire_on_commit=False)
limiter = TokenBucket()
app = FastAPI(title="Limited course seats")


class CourseCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    capacity: int = Field(ge=0, le=1_000_000)


class EnrollRequest(BaseModel):
    email: EmailStr


def get_session() -> Generator[Session, None, None]:
    with SessionLocal() as session:
        yield session


def rate_limit(request: Request) -> None:
    client = request.client.host if request.client else "unknown"
    if not limiter.consume(client):
        raise HTTPException(status_code=429, detail="Too many enrollment attempts")


@app.on_event("startup")
def create_tables() -> None:
    Base.metadata.create_all(engine)


@app.post("/courses", status_code=status.HTTP_201_CREATED)
def create_course(data: CourseCreate, request: Request, session: Session = Depends(get_session)) -> dict[str, object]:
    rate_limit(request)
    course = Course(title=data.title, capacity=data.capacity, remaining_seats=data.capacity)
    session.add(course)
    session.commit()
    return {"id": course.id, "title": course.title, "capacity": course.capacity, "remaining_seats": course.remaining_seats}


@app.post("/courses/{course_id}/enrollments", status_code=status.HTTP_201_CREATED)
def enroll(course_id: int, data: EnrollRequest, request: Request, session: Session = Depends(get_session)) -> dict[str, object]:
    """Reserve a seat and create enrollment as one PostgreSQL transaction."""
    rate_limit(request)
    email = data.email.lower()
    try:
        # This avoids a separate read-then-insert race for first-time students.
        session.execute(insert(Student).values(email=email).on_conflict_do_nothing(index_elements=[Student.email]))

        # Every competing reservation for this course waits here, then sees new availability.
        course = session.scalar(select(Course).where(Course.id == course_id).with_for_update())
        if course is None:
            session.rollback()
            raise HTTPException(status_code=404, detail="Course not found")
        student = session.scalar(select(Student).where(Student.email == email))
        assert student is not None
        existing = session.scalar(
            select(Enrollment).where(Enrollment.student_id == student.id, Enrollment.course_id == course.id)
        )
        if existing is not None:
            session.commit()
            return {"enrollment_id": existing.id, "course_id": course.id, "status": "already_enrolled", "remaining_seats": course.remaining_seats}
        if course.remaining_seats <= 0:
            session.rollback()
            raise HTTPException(status_code=409, detail="Course is full")

        enrollment = Enrollment(student_id=student.id, course_id=course.id)
        session.add(enrollment)
        course.remaining_seats -= 1
        session.commit()
        return {"enrollment_id": enrollment.id, "course_id": course.id, "status": "enrolled", "remaining_seats": course.remaining_seats}
    except HTTPException:
        raise
    except Exception as exc:
        session.rollback()
        raise HTTPException(status_code=503, detail="Could not reserve a course seat") from exc


@app.get("/courses/{course_id}")
def availability(course_id: int, session: Session = Depends(get_session)) -> dict[str, object]:
    course = session.get(Course, course_id)
    if course is None:
        raise HTTPException(status_code=404, detail="Course not found")
    return {"id": course.id, "title": course.title, "capacity": course.capacity, "remaining_seats": course.remaining_seats}
