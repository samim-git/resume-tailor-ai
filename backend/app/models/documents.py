"""Beanie ODM Document models for MongoDB."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from beanie import Document, Indexed, Update, before_event, Insert, Replace
from pydantic import Field

from .schemas_resume import ResumeStructured
from .schemas_template import ResumeTemplateSchema, TemplateBlock, TemplateTheme


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


class TailoredCoverLetter(TimestampedDocument):
    """Tailored cover letter document. Saved when generating a cover letter for a job."""

    title: str
    job_title: str
    job_description: str
    tailored_content: str
    user_id: str
    ai_template_message: Optional[str] = None

    class Settings:
        name = "tailored_cover_letter"


class ResumeTemplate(TimestampedDocument):
    """Resume template definition. Collection: resume_template."""

    name: str = Field(default="Default")
    version: int = Field(default=1, ge=1)
    is_default: bool = Field(default=False)

    theme: TemplateTheme = Field(default_factory=TemplateTheme)
    blocks: list[TemplateBlock] = Field(default_factory=list)

    class Settings:
        name = "resume_template"


class BuiltResume(TimestampedDocument):
    """User-built resume draft. Collection: built_resumes."""

    user_id: str
    title: str = Field(default="Untitled")
    resume: ResumeStructured
    template_id: Optional[str] = Field(default=None, description="Selected resume template id for this built resume")

    class Settings:
        name = "built_resumes"
