"""
Course materials file upload.

Students upload PDFs and videos (up to 500MB). Bytes go to S3-compatible
storage; metadata is recorded in PostgreSQL.
"""

import os
import uuid
from datetime import datetime
from typing import Optional

import boto3
from fastapi import Depends, FastAPI, File, Form, HTTPException, UploadFile
from sqlalchemy import Column, DateTime, Integer, String, create_engine
from sqlalchemy.orm import Session, declarative_base, sessionmaker

DATABASE_URL = os.getenv(
    "DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/uploads"
)
S3_ENDPOINT = os.getenv("S3_ENDPOINT", "http://localhost:9000")
S3_ACCESS_KEY = os.getenv("S3_ACCESS_KEY", "minioadmin")
S3_SECRET_KEY = os.getenv("S3_SECRET_KEY", "minioadmin")
S3_BUCKET = os.getenv("S3_BUCKET", "course-materials")
S3_REGION = os.getenv("S3_REGION", "us-east-1")

MAX_BYTES = 500 * 1024 * 1024
ALLOWED_TYPES = {
    "application/pdf",
    "video/mp4",
    "video/webm",
    "video/quicktime",
    "video/x-msvideo",
}

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()
app = FastAPI(title="Course material upload")

s3 = boto3.client(
    "s3",
    endpoint_url=S3_ENDPOINT,
    aws_access_key_id=S3_ACCESS_KEY,
    aws_secret_access_key=S3_SECRET_KEY,
    region_name=S3_REGION,
)


class Material(Base):
    __tablename__ = "materials"

    id = Column(Integer, primary_key=True)
    course_id = Column(Integer, nullable=False, index=True)
    student_id = Column(Integer, nullable=True)
    filename = Column(String, nullable=False)
    content_type = Column(String, nullable=False)
    size_bytes = Column(Integer, nullable=False)
    s3_key = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)
    try:
        s3.create_bucket(Bucket=S3_BUCKET)
    except Exception:
        pass


@app.post("/uploads")
async def upload(
    course_id: int = Form(...),
    student_id: Optional[int] = Form(default=None),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    content_type = file.content_type or "application/octet-stream"
    if content_type not in ALLOWED_TYPES:
        raise HTTPException(status_code=415, detail="Only PDFs and videos are allowed")

    data = await file.read()
    size = len(data)
    if size > MAX_BYTES:
        raise HTTPException(status_code=413, detail="File exceeds 500MB limit")
    if size == 0:
        raise HTTPException(status_code=400, detail="Empty file")

    key = f"courses/{course_id}/{uuid.uuid4()}/{file.filename or 'material'}"
    s3.put_object(
        Bucket=S3_BUCKET,
        Key=key,
        Body=data,
        ContentType=content_type,
    )

    material = Material(
        course_id=course_id,
        student_id=student_id,
        filename=file.filename or "material",
        content_type=content_type,
        size_bytes=size,
        s3_key=key,
    )
    db.add(material)
    db.commit()
    db.refresh(material)

    return {
        "id": material.id,
        "course_id": material.course_id,
        "filename": material.filename,
        "content_type": material.content_type,
        "size_bytes": material.size_bytes,
        "s3_key": material.s3_key,
    }


@app.get("/uploads/{material_id}")
def get_material(material_id: int, db: Session = Depends(get_db)):
    material = db.query(Material).filter(Material.id == material_id).first()
    if not material:
        raise HTTPException(status_code=404, detail="Not found")
    url = s3.generate_presigned_url(
        "get_object",
        Params={"Bucket": S3_BUCKET, "Key": material.s3_key},
        ExpiresIn=3600,
    )
    return {
        "id": material.id,
        "course_id": material.course_id,
        "filename": material.filename,
        "content_type": material.content_type,
        "size_bytes": material.size_bytes,
        "s3_key": material.s3_key,
        "download_url": url,
    }


@app.get("/courses/{course_id}/uploads")
def list_course_materials(course_id: int, db: Session = Depends(get_db)):
    rows = (
        db.query(Material)
        .filter(Material.course_id == course_id)
        .order_by(Material.id.desc())
        .all()
    )
    return [
        {
            "id": m.id,
            "filename": m.filename,
            "content_type": m.content_type,
            "size_bytes": m.size_bytes,
            "s3_key": m.s3_key,
        }
        for m in rows
    ]
