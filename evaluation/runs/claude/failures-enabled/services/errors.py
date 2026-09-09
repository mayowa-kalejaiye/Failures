class ServiceError(Exception):
    """Base class for domain-level errors raised by the service layer."""


class CourseNotFoundError(ServiceError):
    pass


class AlreadyPaidError(ServiceError):
    """A completed payment (and therefore enrollment) already exists for this
    student + course. Charging again would violate I2."""


class PaymentAmountMismatchError(ServiceError):
    """Paystack reported success, but for a different amount/currency than the
    order. We must not grant access to a mismatched charge (I1)."""
