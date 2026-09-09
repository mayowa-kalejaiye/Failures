from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from db import Base
from models._ids import new_uuid


class Enrollment(Base):
    """Grants a student access to a course.

    ``UNIQUE(student_id, course_id)`` makes the grant idempotent: a duplicate
    webhook, a retry, or the reconciler racing the webhook can all *attempt*
    to enroll, but only one row can ever exist (I2 / concurrency).

    ``payment_id`` records *which* verified payment authorised access, so every
    enrollment is traceable back to a completed payment (I1).
    """

    __tablename__ = "enrollments"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    student_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    course_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    payment_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("payments.id"), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    __table_args__ = (
        UniqueConstraint("student_id", "course_id", name="uq_enrollment_student_course"),
    )
