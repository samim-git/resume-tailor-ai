"""Beanie ODM Document models for MongoDB."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from beanie import Document, Indexed, Update, before_event, Insert, Replace
from pydantic import Field

from .schemas_resume import ResumeStructured


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class TimestampedDocument(Document):
    created_at: datetime = Field(default_factory=_utcnow)
    updated_at: datetime = Field(default_factory=_utcnow)

    @before_event(Insert)
    def set_created_at(self):
        now = _utcnow()
        self.created_at = now
        self.updated_at = now

    @before_event(Replace, Update)
    def set_updated_at(self):
        self.updated_at = _utcnow()


class User(TimestampedDocument):
    """User document. Collection: users."""

    fullname: str = ""
    username: Indexed(str, unique=True)
    password: str
    prof: Optional[ResumeStructured] = None

    class Settings:
        name = "users"


class Resume(TimestampedDocument):
    """Resume document. Collection: resumes."""

    title: str
    file_link: str
    version: int = 1
    user_id: Optional[str] = Field(None, description="Link to user id")

    class Settings:
        name = "resumes"


class CoverLetter(TimestampedDocument):
    """Cover letter document. Collection: coverletter."""

    title: str
    file_link: str
    version: int = 1
    user_id: Optional[str] = Field(None, description="Link to user id")

    class Settings:
        name = "coverletter"


class TailoredResume(TimestampedDocument):
    """Tailored resume document. Saved when tailoring for a job."""

    title: str
    job_title: str
    tailored_prof: ResumeStructured
    user_id: str

    class Settings:
        name = "tailored_resume"
