"""Idempotent enrollment grant."""
from __future__ import annotations

import logging

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from models import Enrollment

log = logging.getLogger("enrollment")


async def grant_enrollment(
    session: AsyncSession,
    *,
    student_id: int,
    course_id: int,
    payment_id: str,
) -> Enrollment:
    """Grant access, idempotently.

    Must be called *inside* an already-open transaction (it is part of the
    same atomic unit as marking the payment completed). We first look for an
    existing enrollment, then insert inside a SAVEPOINT so that a lost race on
    the UNIQUE(student, course) constraint rolls back only the insert - not the
    caller's whole transaction - and we return the winning row.
    """
    existing = await session.scalar(
        select(Enrollment).where(
            Enrollment.student_id == student_id,
            Enrollment.course_id == course_id,
        )
    )
    if existing is not None:
        return existing

    enrollment = Enrollment(
        student_id=student_id, course_id=course_id, payment_id=payment_id
    )
    session.add(enrollment)
    try:
        async with session.begin_nested():  # SAVEPOINT
            await session.flush()
    except IntegrityError:
        # A concurrent grant won the unique constraint; adopt its row.
        log.info("enrollment race for student=%s course=%s; using existing",
                 student_id, course_id)
        existing = await session.scalar(
            select(Enrollment).where(
                Enrollment.student_id == student_id,
                Enrollment.course_id == course_id,
            )
        )
        if existing is None:  # pragma: no cover - should be unreachable
            raise
        return existing
    return enrollment
