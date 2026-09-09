"""Pydantic request/response schemas."""
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from .models import PaymentStatus


# --- Auth / users ---
class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    full_name: str | None = None


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: EmailStr
    full_name: str | None
    is_admin: bool
    created_at: datetime


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


# --- Courses ---
class CourseCreate(BaseModel):
    title: str
    slug: str = Field(pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
    description: str | None = None
    price: Decimal = Field(gt=0, max_digits=12, decimal_places=2)
    currency: str = Field(default="NGN", min_length=3, max_length=3)
    content: str | None = None
    is_published: bool = True


class CourseOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    slug: str
    description: str | None
    price: Decimal
    currency: str
    is_published: bool


class CourseContentOut(BaseModel):
    """Returned only to enrolled students."""

    course_id: int
    title: str
    content: str | None


# --- Payments / checkout ---
class CheckoutOut(BaseModel):
    """Returned to the client so it can redirect the browser to Paystack."""

    authorization_url: str
    reference: str
    payment_id: int
    amount: Decimal
    currency: str


class PaymentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    reference: str
    course_id: int
    amount: Decimal
    currency: str
    status: PaymentStatus
    paid_at: datetime | None
    created_at: datetime


class PaymentResultOut(BaseModel):
    """Human-friendly result surfaced from callback / verify."""

    reference: str
    status: PaymentStatus
    enrolled: bool
    course_id: int
    message: str


# --- Enrollments ---
class EnrollmentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    course_id: int
    payment_id: int | None
    created_at: datetime
