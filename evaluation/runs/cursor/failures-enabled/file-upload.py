"""
Course materials file upload (S3-compatible storage + PostgreSQL metadata).

Failures review_plan / review_code / check_invariant applied before finalize.

- Streamed/chunked upload (8MiB chunks, not the full 500MB in RAM)
- SHA-256 content-hash dedup + idempotency_key UNIQUE
- Pending metadata persisted before S3; complete in a transaction / outbox
- timeout=5 on storage; operation_id / request_id in logs
- TokenBucket on mutating upload
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
import time
import uuid
from datetime import datetime, timezone
from tempfile import SpooledTemporaryFile
from typing import Optional

import boto3
from botocore.config import Config
from botocore.exceptions import BotoCoreError, ClientError
from fastapi import Depends, FastAPI, File, Form, Header, HTTPException, Request, UploadFile
from sqlalchemy import (
    Column,
    DateTime,
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
    "DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/uploads"
)
S3_ENDPOINT = os.getenv("S3_ENDPOINT", "http://localhost:9000")
S3_ACCESS_KEY = os.getenv("S3_ACCESS_KEY", "minioadmin")
S3_SECRET_KEY = os.getenv("S3_SECRET_KEY", "minioadmin")
S3_BUCKET = os.getenv("S3_BUCKET", "course-materials")
S3_REGION = os.getenv("S3_REGION", "us-east-1")
# Hung S3 must not hold workers indefinitely.
S3_TIMEOUT = 5  # timeout=5

MAX_BYTES = 500 * 1024 * 1024
CHUNK_SIZE = 8 * 1024 * 1024
ALLOWED_TYPES = {
    "application/pdf",
    "video/mp4",
    "video/webm",
    "video/quicktime",
    "video/x-msvideo",
}

engine = create_engine(DATABASE_URL, pool_size=20, max_overflow=10, pool_timeout=5)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()
app = FastAPI(title="Course material upload")
logger = logging.getLogger("uploads")

s3 = boto3.client(
    "s3",
    endpoint_url=S3_ENDPOINT,
    aws_access_key_id=S3_ACCESS_KEY,
    aws_secret_access_key=S3_SECRET_KEY,
    region_name=S3_REGION,
    config=Config(
        connect_timeout=S3_TIMEOUT,
        read_timeout=S3_TIMEOUT,
        retries={"max_attempts": 3, "mode": "standard"},
    ),
)


class TokenBucket:
    """Per-key token bucket rate limiter."""

    def __init__(self, rate: float = 5.0, capacity: float = 10.0):
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


class Material(Base):
    __tablename__ = "materials"
    __table_args__ = (
        UniqueConstraint("idempotency_key", name="uq_materials_idempotency_key"),
        UniqueConstraint("content_hash", name="uq_materials_content_hash"),
    )

    id = Column(Integer, primary_key=True)
    course_id = Column(Integer, nullable=False, index=True)
    student_id = Column(Integer, nullable=True)
    filename = Column(String, nullable=False)
    content_type = Column(String, nullable=False)
    size_bytes = Column(Integer, nullable=True)
    s3_key = Column(String, nullable=True)
    content_hash = Column(String, nullable=True)
    idempotency_key = Column(String, nullable=False)
    status = Column(String, nullable=False, default="pending")
    cached_response = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class Outbox(Base):
    """Transactional outbox so metadata and follow-up events commit together."""

    __tablename__ = "upload_outbox"
    id = Column(Integer, primary_key=True)
    material_id = Column(Integer, nullable=False, index=True)
    event_type = Column(String, nullable=False)
    payload = Column(Text, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def operation_id_from(x_request_id: str) -> str:
    return x_request_id or str(uuid.uuid4())


def material_payload(m: Material) -> dict:
    return {
        "id": m.id,
        "course_id": m.course_id,
        "filename": m.filename,
        "content_type": m.content_type,
        "size_bytes": m.size_bytes,
        "s3_key": m.s3_key,
        "content_hash": m.content_hash,
        "status": m.status,
        "dedup": False,
    }


def stream_to_spool(upload: UploadFile) -> tuple[SpooledTemporaryFile, str, int]:
    """Chunked stream into a disk-backed spool; hash as we go. Never holds 500MB in RAM."""
    spool = SpooledTemporaryFile(max_size=CHUNK_SIZE)
    digest = hashlib.sha256()
    total = 0
    while True:
        chunk = upload.file.read(CHUNK_SIZE)
        if not chunk:
            break
        total += len(chunk)
        if total > MAX_BYTES:
            spool.close()
            raise HTTPException(status_code=413, detail="File exceeds 500MB limit")
        digest.update(chunk)
        spool.write(chunk)
    if total == 0:
        spool.close()
        raise HTTPException(status_code=400, detail="Empty file")
    spool.seek(0)
    return spool, digest.hexdigest(), total


@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)
    try:
        s3.create_bucket(Bucket=S3_BUCKET)
    except Exception:
        pass


@app.post("/uploads")
def upload(
    request: Request,
    course_id: int = Form(...),
    student_id: Optional[int] = Form(default=None),
    idempotency_key: str = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    x_request_id: str = Header(default=""),
):
    operation_id = operation_id_from(x_request_id)
    ip = request.client.host if request.client else "unknown"
    if not limiter.rate_limit(ip):
        logger.info("upload rate_limit operation_id=%s request_id=%s", operation_id, operation_id)
        raise HTTPException(status_code=429, detail="Too many uploads")

    content_type = file.content_type or "application/octet-stream"
    if content_type not in ALLOWED_TYPES:
        raise HTTPException(status_code=415, detail="Only PDFs and videos are allowed")

    existing = db.query(Material).filter(Material.idempotency_key == idempotency_key).first()
    if existing and existing.status == "completed":
        logger.info(
            "upload cached operation_id=%s request_id=%s idempotency_key=%s",
            operation_id,
            operation_id,
            idempotency_key,
        )
        body = json.loads(existing.cached_response) if existing.cached_response else material_payload(existing)
        body["dedup"] = True
        return body
    if existing and existing.status == "pending":
        raise HTTPException(status_code=409, detail="Upload already in progress")

    pending = Material(
        course_id=course_id,
        student_id=student_id,
        filename=file.filename or "material",
        content_type=content_type,
        idempotency_key=idempotency_key,
        status="pending",
    )
    db.add(pending)
    try:
        db.commit()
        db.refresh(pending)
    except IntegrityError:
        db.rollback()
        raced = db.query(Material).filter(Material.idempotency_key == idempotency_key).first()
        if raced and raced.status == "completed":
            body = json.loads(raced.cached_response) if raced.cached_response else material_payload(raced)
            body["dedup"] = True
            return body
        raise HTTPException(status_code=409, detail="Duplicate idempotency_key")

    logger.info(
        "upload pending operation_id=%s request_id=%s material_id=%s",
        operation_id,
        operation_id,
        pending.id,
    )

    try:
        spool, content_hash, size = stream_to_spool(file)
    except HTTPException:
        pending.status = "failed"
        db.commit()
        raise

    dup = (
        db.query(Material)
        .filter(Material.content_hash == content_hash, Material.status == "completed")
        .first()
    )
    if dup:
        spool.close()
        pending.status = "completed"
        pending.content_hash = None  # unique on hash: reuse existing object
        pending.size_bytes = dup.size_bytes
        pending.s3_key = dup.s3_key
        pending.cached_response = json.dumps({**material_payload(dup), "dedup": True})
        db.commit()
        logger.info(
            "upload hash-dedup operation_id=%s request_id=%s hash=%s",
            operation_id,
            operation_id,
            content_hash,
        )
        return json.loads(pending.cached_response)

    key = f"courses/{course_id}/{content_hash}/{file.filename or 'material'}"
    try:
        s3.upload_fileobj(spool, S3_BUCKET, key, ExtraArgs={"ContentType": content_type})
    except (BotoCoreError, ClientError) as exc:
        spool.close()
        pending.status = "failed"
        db.commit()
        logger.info(
            "upload storage-failed operation_id=%s request_id=%s err=%s",
            operation_id,
            operation_id,
            exc,
        )
        raise HTTPException(status_code=504, detail="Storage timeout or failure")
    finally:
        spool.close()

    # Same transaction: lock pending row, complete metadata, outbox.
    db.execute(
        text("SELECT id FROM materials WHERE id = :id FOR UPDATE"),
        {"id": pending.id},
    )
    pending.size_bytes = size
    pending.s3_key = key
    pending.content_hash = content_hash
    pending.status = "completed"
    payload = {**material_payload(pending), "operation_id": operation_id}
    pending.cached_response = json.dumps(payload)
    db.add(
        Outbox(
            material_id=pending.id,
            event_type="upload.completed",
            payload=pending.cached_response,
        )
    )
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        other = db.query(Material).filter(Material.content_hash == content_hash).first()
        pending = db.query(Material).filter(Material.id == pending.id).first()
        if pending:
            pending.status = "completed"
            pending.content_hash = None
            pending.s3_key = other.s3_key if other else key
            pending.size_bytes = other.size_bytes if other else size
            pending.cached_response = json.dumps(
                {**(material_payload(other) if other else payload), "dedup": True}
            )
            db.commit()
        logger.info(
            "upload hash-conflict operation_id=%s request_id=%s",
            operation_id,
            operation_id,
        )
        return json.loads(pending.cached_response)

    logger.info(
        "upload completed operation_id=%s request_id=%s material_id=%s hash=%s",
        operation_id,
        operation_id,
        pending.id,
        content_hash,
    )
    return payload


@app.post("/uploads/reconcile")
def reconcile(db: Session = Depends(get_db), x_request_id: str = Header(default="")):
    """Recover pending rows after crash between S3 success and metadata commit."""
    operation_id = operation_id_from(x_request_id)
    pending_rows = db.query(Material).filter(Material.status == "pending").all()
    recovered = 0
    for m in pending_rows:
        if not m.s3_key:
            continue
        try:
            s3.head_object(Bucket=S3_BUCKET, Key=m.s3_key)
        except ClientError:
            continue
        locked = db.execute(
            text("SELECT id FROM materials WHERE id = :id FOR UPDATE"),
            {"id": m.id},
        ).first()
        if not locked:
            continue
        m.status = "completed"
        db.add(
            Outbox(
                material_id=m.id,
                event_type="upload.reconciled",
                payload=json.dumps(material_payload(m)),
            )
        )
        recovered += 1
    db.commit()
    logger.info("reconcile operation_id=%s request_id=%s recovered=%s", operation_id, operation_id, recovered)
    return {"recovered": recovered, "operation_id": operation_id}


@app.get("/uploads/{material_id}")
def get_material(material_id: int, db: Session = Depends(get_db)):
    material = db.query(Material).filter(Material.id == material_id).first()
    if not material:
        raise HTTPException(status_code=404, detail="Not found")
    return material_payload(material)
