"""Import every model so that ``Base.metadata`` is fully populated whenever
this package is imported (needed by ``create_all`` and Alembic autogenerate)."""
from models.course import Course
from models.enrollment import Enrollment
from models.payment import Payment, PaymentStatus
from models.webhook_event import WebhookEvent

__all__ = [
    "Course",
    "Enrollment",
    "Payment",
    "PaymentStatus",
    "WebhookEvent",
]
