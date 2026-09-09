"""Course routes: list/detail (public), create (admin), content (enrolled only)."""
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.security import CurrentUser, require_admin
from ..database import get_session
from ..models import Course, Enrollment, User
from ..schemas import CourseContentOut, CourseCreate, CourseOut

router = APIRouter(prefix="/courses", tags=["courses"])

SessionDep = Annotated[AsyncSession, Depends(get_session)]


@router.get("", response_model=list[CourseOut])
async def list_courses(session: SessionDep) -> list[Course]:
    result = await session.scalars(
        select(Course).where(Course.is_published.is_(True)).order_by(Course.id)
    )
    return list(result)


@router.get("/{course_id}", response_model=CourseOut)
async def get_course(course_id: int, session: SessionDep) -> Course:
    course = await session.get(Course, course_id)
    if course is None or not course.is_published:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Course not found")
    return course


@router.post("", response_model=CourseOut, status_code=status.HTTP_201_CREATED)
async def create_course(
    payload: CourseCreate,
    session: SessionDep,
    _admin: Annotated[User, Depends(require_admin)],
) -> Course:
    course = Course(
        title=payload.title,
        slug=payload.slug,
        description=payload.description,
        price=payload.price,
        currency=payload.currency.upper(),
        content=payload.content,
        is_published=payload.is_published,
    )
    session.add(course)
    try:
        await session.commit()
    except IntegrityError:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="A course with that slug already exists"
        )
    await session.refresh(course)
    return course


@router.get("/{course_id}/content", response_model=CourseContentOut)
async def get_course_content(
    course_id: int, session: SessionDep, user: CurrentUser
) -> CourseContentOut:
    """The protected material a student unlocks after paying. 403 if not enrolled."""
    course = await session.get(Course, course_id)
    if course is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Course not found")

    enrollment = await session.scalar(
        select(Enrollment).where(
            Enrollment.user_id == user.id, Enrollment.course_id == course_id
        )
    )
    if enrollment is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You must enroll (pay) for this course to access its content",
        )
    return CourseContentOut(course_id=course.id, title=course.title, content=course.content)
