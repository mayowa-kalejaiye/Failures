"""FastAPI course-material uploads backed by PostgreSQL and S3-compatible storage.

Required configuration: DATABASE_URL, S3_BUCKET, AWS_ACCESS_KEY_ID,
AWS_SECRET_ACCESS_KEY.  S3_ENDPOINT_URL is optional for MinIO/other compatible
services.  Uploads are streamed in 8 MiB multipart chunks and capped at 500 MiB.
"""

from __future__ import annotations

import mimetypes
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Generator

import boto3
from botocore.client import BaseClient
from fastapi import Depends, FastAPI, File, Form, HTTPException, Request, UploadFile, status
from sqlalchemy import DateTime, ForeignKey, Integer, String, create_engine, select
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, sessionmaker


DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+psycopg://postgres:postgres@localhost/courses")
S3_BUCKET = os.getenv("S3_BUCKET", "course-materials")
S3_ENDPOINT_URL = os.getenv("S3_ENDPOINT_URL")
MAX_UPLOAD_BYTES = 500 * 1024 * 1024
CHUNK_SIZE = 8 * 1024 * 1024
ALLOWED_PDF = {"application/pdf"}


class Base(DeclarativeBase):
    pass


class Student(Base):
    __tablename__ = "students"
    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(320), unique=True)


class Course(Base):
    __tablename__ = "courses"
    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(200))


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


engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(engine, expire_on_commit=False)
s3: BaseClient = boto3.client("s3", endpoint_url=S3_ENDPOINT_URL)
app = FastAPI(title="Course material uploads")


def get_session() -> Generator[Session, None, None]:
    with SessionLocal() as session:
        yield session


def reject_oversized_content_length(request: Request) -> None:
    value = request.headers.get("content-length")
    if value and value.isdigit() and int(value) > MAX_UPLOAD_BYTES + 1024 * 1024:
        # The multipart envelope is small, so allow one MiB for its fields/boundary.
        raise HTTPException(status_code=413, detail="Upload exceeds the 500 MB limit")


def validated_content_type(upload: UploadFile) -> str:
    filename = upload.filename or "upload"
    declared = (upload.content_type or "").lower()
    inferred, _ = mimetypes.guess_type(filename)
    content_type = declared or inferred or "application/octet-stream"
    is_pdf = content_type in ALLOWED_PDF and filename.lower().endswith(".pdf")
    is_video = content_type.startswith("video/") and Path(filename).suffix.lower() in {".mp4", ".mov", ".webm", ".mkv", ".avi"}
    if not (is_pdf or is_video):
        raise HTTPException(status_code=415, detail="Only PDF and video uploads are supported")
    return content_type


def upload_to_s3(upload: UploadFile, storage_key: str, content_type: str) -> int:
    """Stream a multipart object; abort it if the client exceeds the size limit."""
    multipart = s3.create_multipart_upload(Bucket=S3_BUCKET, Key=storage_key, ContentType=content_type)
    upload_id = multipart["UploadId"]
    parts: list[dict[str, object]] = []
    total = 0
    try:
        while chunk := upload.file.read(CHUNK_SIZE):
            total += len(chunk)
            if total > MAX_UPLOAD_BYTES:
                raise HTTPException(status_code=413, detail="Upload exceeds the 500 MB limit")
            part_number = len(parts) + 1
            result = s3.upload_part(Bucket=S3_BUCKET, Key=storage_key, UploadId=upload_id, PartNumber=part_number, Body=chunk)
            parts.append({"PartNumber": part_number, "ETag": result["ETag"]})
        if total == 0:
            raise HTTPException(status_code=400, detail="Upload is empty")
        s3.complete_multipart_upload(Bucket=S3_BUCKET, Key=storage_key, UploadId=upload_id, MultipartUpload={"Parts": parts})
        return total
    except Exception:
        s3.abort_multipart_upload(Bucket=S3_BUCKET, Key=storage_key, UploadId=upload_id)
        raise


@app.on_event("startup")
def create_tables() -> None:
    Base.metadata.create_all(engine)


@app.post("/course-materials", status_code=status.HTTP_201_CREATED)
def upload_course_material(
    request: Request,
    course_id: int = Form(...),
    student_id: int = Form(...),
    file: UploadFile = File(...),
    session: Session = Depends(get_session),
) -> dict[str, object]:
    reject_oversized_content_length(request)
    if session.get(Course, course_id) is None or session.get(Student, student_id) is None:
        raise HTTPException(status_code=404, detail="Course or student not found")
    content_type = validated_content_type(file)
    material_id = str(uuid.uuid4())
    safe_extension = Path(file.filename or "").suffix.lower()
    storage_key = f"courses/{course_id}/materials/{material_id}{safe_extension}"
    try:
        size_bytes = upload_to_s3(file, storage_key, content_type)
        material = CourseMaterial(
            id=material_id,
            course_id=course_id,
            uploaded_by_student_id=student_id,
            original_filename=Path(file.filename or "upload").name,
            content_type=content_type,
            size_bytes=size_bytes,
            storage_key=storage_key,
        )
        session.add(material)
        session.commit()
    except HTTPException:
        raise
    except Exception as exc:
        session.rollback()
        # Metadata failure must not leave a permanent, untracked object behind.
        try:
            s3.delete_object(Bucket=S3_BUCKET, Key=storage_key)
        except Exception:
            pass
        raise HTTPException(status_code=502, detail="Could not store upload") from exc
    finally:
        file.file.close()
    return {
        "id": material.id,
        "course_id": material.course_id,
        "filename": material.original_filename,
        "content_type": material.content_type,
        "size_bytes": material.size_bytes,
    }


@app.get("/course-materials/{material_id}")
def material_metadata(material_id: str, session: Session = Depends(get_session)) -> dict[str, object]:
    material = session.get(CourseMaterial, material_id)
    if material is None:
        raise HTTPException(status_code=404, detail="Material not found")
    return {
        "id": material.id,
        "course_id": material.course_id,
        "filename": material.original_filename,
        "content_type": material.content_type,
        "size_bytes": material.size_bytes,
        "storage_key": material.storage_key,
    }
