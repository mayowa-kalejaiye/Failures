"""
Limited course-seat inventory.

Students enroll until seats run out. PostgreSQL stores courses and
enrollments; concurrent requests share a connection pool.
"""

import os
from datetime import datetime

from fastapi import Depends, FastAPI, HTTPException
from pydantic import BaseModel, EmailStr
from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, create_engine
from sqlalchemy.orm import Session, declarative_base, sessionmaker

DATABASE_URL = os.getenv(
    "DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/inventory"
)

engine = create_engine(DATABASE_URL, pool_size=20, max_overflow=40)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()
app = FastAPI(title="Course seats")


class Course(Base):
    __tablename__ = "courses"

    id = Column(Integer, primary_key=True)
    title = Column(String, nullable=False)
    capacity = Column(Integer, nullable=False)
    remaining_seats = Column(Integer, nullable=False)


class Student(Base):
    __tablename__ = "students"

    id = Column(Integer, primary_key=True)
    email = Column(String, unique=True, nullable=False)


class Enrollment(Base):
    __tablename__ = "enrollments"

    id = Column(Integer, primary_key=True)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False)
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class CourseCreate(BaseModel):
    title: str
    capacity: int


class EnrollRequest(BaseModel):
    email: EmailStr


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)


@app.post("/courses", status_code=201)
def create_course(payload: CourseCreate, db: Session = Depends(get_db)):
    if payload.capacity < 0:
        raise HTTPException(status_code=400, detail="Capacity must be >= 0")
    course = Course(
        title=payload.title,
        capacity=payload.capacity,
        remaining_seats=payload.capacity,
    )
    db.add(course)
    db.commit()
    db.refresh(course)
    return {
        "id": course.id,
        "title": course.title,
        "capacity": course.capacity,
        "remaining_seats": course.remaining_seats,
    }


@app.post("/courses/{course_id}/enrollments", status_code=201)
def enroll(course_id: int, payload: EnrollRequest, db: Session = Depends(get_db)):
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    student = db.query(Student).filter(Student.email == payload.email.lower()).first()
    if not student:
        student = Student(email=payload.email.lower())
        db.add(student)
        db.flush()

    if course.remaining_seats <= 0:
        raise HTTPException(status_code=409, detail="Course is full")

    course.remaining_seats = course.remaining_seats - 1
    enrollment = Enrollment(student_id=student.id, course_id=course.id)
    db.add(enrollment)
    db.commit()
    db.refresh(enrollment)
    return {
        "enrollment_id": enrollment.id,
        "course_id": course.id,
        "student_id": student.id,
        "remaining_seats": course.remaining_seats,
    }


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
    }
