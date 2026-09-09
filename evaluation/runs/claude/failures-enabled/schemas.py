from pydantic import BaseModel, EmailStr, Field

from models import PaymentStatus


class InitializePaymentRequest(BaseModel):
    student_id: int = Field(..., gt=0)
    email: EmailStr
    course_id: int = Field(..., gt=0)


class InitializePaymentResponse(BaseModel):
    payment_id: str
    reference: str
    status: PaymentStatus
    authorization_url: str | None
    # Echo the key so a client that let the server generate one can reuse it on
    # retry to get the same payment back.
    idempotency_key: str


class PaymentStatusResponse(BaseModel):
    payment_id: str
    reference: str
    status: PaymentStatus
    course_id: int
    student_id: int
    enrolled: bool
