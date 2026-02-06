"""Repository layer using Beanie ODM for database operations."""

from __future__ import annotations

from typing import Optional

from ..models.documents import CoverLetter, Resume, TailoredResume, User
from ..models.schemas_resume import ResumeStructured as ResumeSchema


async def save_user_prof(user_id: str, prof: ResumeSchema) -> str:
    """
    Update user's prof with extracted resume data.
    Returns user_id.
    Raises ValueError if user does not exist.
    """
    user = await User.get(user_id)
    if not user:
        raise ValueError(f"User {user_id} not found")
    user.prof = prof
    await user.save()
    return user_id


async def save_tailored_resume(
    user_id: str,
    title: str,
    job_title: str,
    tailored_prof: ResumeSchema,
) -> str:
    """
    Save a tailored resume for a job.
    Returns tailored_resume id.
    """
    tailored = TailoredResume(
        title=title,
        job_title=job_title,
        tailored_prof=tailored_prof,
        user_id=user_id,
    )
    await tailored.insert()
    return str(tailored.id)


async def create_user(fullname: str, username: str, password: str) -> str:
    """Create a new user. Returns user id."""
    user = User(
        fullname=fullname,
        username=username,
        password=password,  # Should be hashed in production
        prof=None,
    )
    await user.insert()
    return str(user.id)


async def get_user_by_id(user_id: str) -> Optional[User]:
    """Get user by id."""
    return await User.get(user_id)


async def get_user_by_username(username: str) -> Optional[User]:
    """Get user by username."""
    return await User.find_one(User.username == username)


async def add_resume(
    title: str,
    file_link: str,
    version: int = 1,
    user_id: Optional[str] = None,
) -> str:
    """Add a resume record. Returns resume id."""
    resume = Resume(
        title=title,
        file_link=file_link,
        version=version,
        user_id=user_id,
    )
    await resume.insert()
    return str(resume.id)


async def add_cover_letter(
    title: str,
    file_link: str,
    version: int = 1,
    user_id: Optional[str] = None,
) -> str:
    """Add a cover letter record. Returns cover letter id."""
    cover = CoverLetter(
        title=title,
        file_link=file_link,
        version=version,
        user_id=user_id,
    )
    await cover.insert()
    return str(cover.id)
