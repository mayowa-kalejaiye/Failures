"""Enrollment routes: a student's own access grants."""
from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.security import CurrentUser
from ..database import get_session
from ..models import Enrollment
from ..schemas import EnrollmentOut

router = APIRouter(prefix="/me", tags=["enrollments"])

SessionDep = Annotated[AsyncSession, Depends(get_session)]


@router.get("/enrollments", response_model=list[EnrollmentOut])
async def my_enrollments(session: SessionDep, user: CurrentUser) -> list[Enrollment]:
    result = await session.scalars(
        select(Enrollment)
        .where(Enrollment.user_id == user.id)
        .order_by(Enrollment.created_at.desc())
    )
    return list(result)
