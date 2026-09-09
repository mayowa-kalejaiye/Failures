import enum
from datetime import datetime

from sqlalchemy import (
    BigInteger,
    DateTime,
    Enum as SAEnum,
    Index,
    Integer,
    String,
    func,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column

from db import Base
from models._ids import new_uuid


class PaymentStatus(str, enum.Enum):
    # A payment is a small state machine. The transition pending -> completed
    # happens exactly once, under a row lock, which is the core of I2.
    pending = "pending"
    completed = "completed"
    failed = "failed"


class Payment(Base):
    __tablename__ = "payments"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)

    # Our own reference, sent to Paystack as `reference`. Because it is stable,
    # re-initialising / re-verifying with it is idempotent on Paystack's side,
    # and it is the join key between our record and the transaction.
    reference: Mapped[str] = mapped_column(
        String(64), unique=True, index=True, default=new_uuid, nullable=False
    )

    # Client-supplied key that identifies one logical checkout attempt.
    # UNIQUE => the same attempt retried never creates a second charge (I2).
    idempotency_key: Mapped[str] = mapped_column(
        String(128), unique=True, nullable=False
    )

    student_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    course_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)

    # Amount is in the currency subunit (kobo for NGN). Sourced from the
    # course, never the client - the client cannot tell us what to charge.
    amount: Mapped[int] = mapped_column(BigInteger, nullable=False)
    currency: Mapped[str] = mapped_column(String(8), nullable=False, default="NGN")
    email: Mapped[str] = mapped_column(String(255), nullable=False)

    status: Mapped[PaymentStatus] = mapped_column(
        SAEnum(PaymentStatus, native_enum=False, create_constraint=False,
               length=16, validate_strings=True),
        nullable=False,
        default=PaymentStatus.pending,
        index=True,
    )

    authorization_url: Mapped[str | None] = mapped_column(String(512))
    access_code: Mapped[str | None] = mapped_column(String(128))
    paystack_transaction_id: Mapped[str | None] = mapped_column(String(64))

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
    verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    __table_args__ = (
        # At most ONE active (pending or completed) payment may exist per
        # (student, course). This is the invariant backstop for I2 at the
        # business level: two concurrent "pay for course X" requests cannot
        # both create a charge - one wins the insert, the other is told to
        # resume the existing one. A `failed` row is excluded, so a genuine
        # retry-after-failure is still allowed.
        Index(
            "uq_active_payment_per_course",
            "student_id",
            "course_id",
            unique=True,
            postgresql_where=text("status IN ('pending', 'completed')"),
            sqlite_where=text("status IN ('pending', 'completed')"),
        ),
    )

    def __repr__(self) -> str:  # pragma: no cover - debug aid
        return (
            f"<Payment {self.reference} student={self.student_id} "
            f"course={self.course_id} status={self.status}>"
        )
