"""Idempotent, streaming course-material uploads using FastAPI, PostgreSQL, and S3.

Set DATABASE_URL, S3_BUCKET, AWS_ACCESS_KEY_ID, and AWS_SECRET_ACCESS_KEY.
S3_ENDPOINT_URL supports MinIO and other S3-compatible storage. The API accepts
PDF/video files up to 500 MiB and requires an ``Idempotency-Key`` header.
"""

from __future__ import annotations

import mimetypes
import os
import threading
import time
import uuid
from datetime import datetime, timedelta, timezone
from enum import Enum
from pathlib import Path
from typing import Generator

import boto3
from botocore.client import BaseClient
from botocore.config import Config
from fastapi import Depends, File, Form, Header, HTTPException, Request, UploadFile, status
from fastapi import FastAPI
from sqlalchemy import DateTime, ForeignKey, Integer, String, UniqueConstraint, create_engine, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, sessionmaker


DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+psycopg://postgres:postgres@localhost/courses")
S3_BUCKET = os.getenv("S3_BUCKET", "course-materials")
S3_ENDPOINT_URL = os.getenv("S3_ENDPOINT_URL")
MAX_UPLOAD_BYTES = 500 * 1024 * 1024
CHUNK_SIZE = 8 * 1024 * 1024
UPLOAD_LEASE = timedelta(minutes=30)
VIDEO_EXTENSIONS = {".mp4", ".mov", ".webm", ".mkv", ".avi"}


class Base(DeclarativeBase):
    pass


class UploadState(str, Enum):
    UPLOADING = "uploading"
    COMPLETE = "complete"
    FAILED = "failed"


class Student(Base):
    __tablename__ = "students"
    id: Mapped[int] = mapped_column(primary_key=True)


class Course(Base):
    __tablename__ = "courses"
    id: Mapped[int] = mapped_column(primary_key=True)


class CourseMaterial(Base):
    __tablename__ = "course_materials"
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    course_id: Mapped[int] = mapped_column(ForeignKey("courses.id"), index=True)
    uploaded_by_student_id: Mapped[int] = mapped_column(ForeignKey("students.id"), index=True)
    original_filename: Mapped[str] = mapped_column(String(500))
    content_type: Mapped[str] = mapped_column(String(100))
    size_bytes: Mapped[int] = mapped_column(Integer)
    storage_key: Mapped[str] = mapped_column(String(1000), unique=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


class UploadAttempt(Base):
    __tablename__ = "upload_attempts"
    __table_args__ = (UniqueConstraint("idempotency_key", name="uq_upload_idempotency_key"),)
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    idempotency_key: Mapped[str] = mapped_column(String(255))
    course_id: Mapped[int] = mapped_column(ForeignKey("courses.id"))
    student_id: Mapped[int] = mapped_column(ForeignKey("students.id"))
    material_id: Mapped[str] = mapped_column(String(36), unique=True)
    storage_key: Mapped[str] = mapped_column(String(1000), unique=True)
    state: Mapped[UploadState] = mapped_column(default=UploadState.UPLOADING, index=True)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    last_error: Mapped[str | None] = mapped_column(String(1000), nullable=True)


class TokenBucket:
    def __init__(self, capacity: int = 20, refill_per_second: float = 0.2) -> None:
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
s3: BaseClient = boto3.client("s3", endpoint_url=S3_ENDPOINT_URL, config=Config(connect_timeout=5, read_timeout=30, retries={"max_attempts": 3, "mode": "standard"}))
limiter = TokenBucket()
app = FastAPI(title="Course material uploads")


def get_session() -> Generator[Session, None, None]:
    with SessionLocal() as session:
        yield session


def rate_limit(request: Request) -> None:
    key = request.client.host if request.client else "unknown"
    if not limiter.consume(key):
        raise HTTPException(status_code=429, detail="Too many upload attempts")


def validate_file(upload: UploadFile) -> tuple[str, str]:
    filename = Path(upload.filename or "upload").name
    suffix = Path(filename).suffix.lower()
    declared = (upload.content_type or "").lower()
    inferred, _ = mimetypes.guess_type(filename)
    content_type = declared or inferred or "application/octet-stream"
    if not ((suffix == ".pdf" and content_type == "application/pdf") or (suffix in VIDEO_EXTENSIONS and content_type.startswith("video/"))):
        raise HTTPException(status_code=415, detail="Only PDF and video uploads are supported")
    return filename, content_type


def too_large_from_headers(request: Request) -> bool:
    value = request.headers.get("content-length")
    return bool(value and value.isdigit() and int(value) > MAX_UPLOAD_BYTES + 1024 * 1024)


def stream_to_s3(upload: UploadFile, storage_key: str, content_type: str) -> int:
    multipart = s3.create_multipart_upload(Bucket=S3_BUCKET, Key=storage_key, ContentType=content_type)
    upload_id = multipart["UploadId"]
    parts: list[dict[str, object]] = []
    total = 0
    try:
        while chunk := upload.file.read(CHUNK_SIZE):
            total += len(chunk)
            if total > MAX_UPLOAD_BYTES:
                raise HTTPException(status_code=413, detail="Upload exceeds the 500 MB limit")
            number = len(parts) + 1
            part = s3.upload_part(Bucket=S3_BUCKET, Key=storage_key, UploadId=upload_id, PartNumber=number, Body=chunk)
            parts.append({"PartNumber": number, "ETag": part["ETag"]})
        if not parts:
            raise HTTPException(status_code=400, detail="Upload is empty")
        s3.complete_multipart_upload(Bucket=S3_BUCKET, Key=storage_key, UploadId=upload_id, MultipartUpload={"Parts": parts})
        return total
    except Exception:
        try:
            s3.abort_multipart_upload(Bucket=S3_BUCKET, Key=storage_key, UploadId=upload_id)
        except Exception:
            pass
        raise


def mark_failed(session: Session, attempt_id: str, error: Exception) -> None:
    session.rollback()
    attempt = session.scalar(select(UploadAttempt).where(UploadAttempt.id == attempt_id).with_for_update())
    if attempt is not None and attempt.state != UploadState.COMPLETE:
        attempt.state = UploadState.FAILED
        attempt.last_error = str(error)[:1000]
        session.commit()


def response_for(material: CourseMaterial) -> dict[str, object]:
    return {"id": material.id, "course_id": material.course_id, "filename": material.original_filename, "content_type": material.content_type, "size_bytes": material.size_bytes}


@app.on_event("startup")
def create_tables() -> None:
    Base.metadata.create_all(engine)


@app.post("/course-materials", status_code=status.HTTP_201_CREATED)
def upload_material(
    request: Request,
    course_id: int = Form(...),
    student_id: int = Form(...),
    file: UploadFile = File(...),
    idempotency_key: str = Header(alias="Idempotency-Key", min_length=8, max_length=255),
    session: Session = Depends(get_session),
) -> dict[str, object]:
    rate_limit(request)
    if too_large_from_headers(request):
        raise HTTPException(status_code=413, detail="Upload exceeds the 500 MB limit")
    if session.get(Course, course_id) is None or session.get(Student, student_id) is None:
        raise HTTPException(status_code=404, detail="Course or student not found")
    filename, content_type = validate_file(file)

    material_id = str(uuid.uuid4())
    storage_key = f"courses/{course_id}/materials/{material_id}{Path(filename).suffix.lower()}"
    inserted = session.execute(
        insert(UploadAttempt).values(
            id=str(uuid.uuid4()), idempotency_key=idempotency_key, course_id=course_id, student_id=student_id,
            material_id=material_id, storage_key=storage_key,
        ).on_conflict_do_nothing(index_elements=[UploadAttempt.idempotency_key])
    )
    session.commit()  # Durable idempotency boundary before the external S3 side effect.

    attempt = session.scalar(select(UploadAttempt).where(UploadAttempt.idempotency_key == idempotency_key).with_for_update())
    assert attempt is not None
    if attempt.course_id != course_id or attempt.student_id != student_id:
        raise HTTPException(status_code=409, detail="Idempotency key belongs to a different upload")
    if attempt.state == UploadState.COMPLETE:
        material = session.get(CourseMaterial, attempt.material_id)
        if material is None:
            raise HTTPException(status_code=500, detail="Completed upload metadata is missing")
        return response_for(material)
    now = datetime.now(timezone.utc)
    if inserted.rowcount == 0 and attempt.state == UploadState.UPLOADING and attempt.started_at > now - UPLOAD_LEASE:
        raise HTTPException(status_code=409, detail="Upload with this idempotency key is already in progress")
    attempt.state, attempt.started_at, attempt.last_error = UploadState.UPLOADING, now, None
    session.commit()

    try:
        size_bytes = stream_to_s3(file, attempt.storage_key, content_type)
        locked = session.scalar(select(UploadAttempt).where(UploadAttempt.id == attempt.id).with_for_update())
        if locked is None or locked.state != UploadState.UPLOADING:
            raise RuntimeError("Upload attempt was no longer claimable")
        material = CourseMaterial(
            id=locked.material_id, course_id=course_id, uploaded_by_student_id=student_id,
            original_filename=filename, content_type=content_type, size_bytes=size_bytes, storage_key=locked.storage_key,
        )
        session.add(material)
        locked.state = UploadState.COMPLETE
        session.commit()
        return response_for(material)
    except HTTPException as exc:
        mark_failed(session, attempt.id, exc)
        raise
    except Exception as exc:
        mark_failed(session, attempt.id, exc)
        # S3 completed but PostgreSQL did not: remove the untracked object before retry.
        try:
            latest = session.get(UploadAttempt, attempt.id)
            if latest is None or latest.state != UploadState.COMPLETE:
                s3.delete_object(Bucket=S3_BUCKET, Key=attempt.storage_key)
        except Exception:
            pass
        raise HTTPException(status_code=502, detail="Could not store upload") from exc
    finally:
        file.file.close()


@app.get("/course-materials/{material_id}")
def material_metadata(material_id: str, session: Session = Depends(get_session)) -> dict[str, object]:
    material = session.get(CourseMaterial, material_id)
    if material is None:
        raise HTTPException(status_code=404, detail="Material not found")
    return response_for(material)
