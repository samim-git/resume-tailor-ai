"""Beanie ODM initialization and database connection."""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from beanie import init_beanie
from pymongo import AsyncMongoClient

from ..config import MONGODB_DB_NAME, MONGODB_URI
from ..models.documents import BuiltResume, CoverLetter, Resume, ResumeTemplate, TailoredCoverLetter, TailoredResume, User

_db_client: AsyncMongoClient | None = None


async def init_db() -> None:
    """Initialize Beanie ODM with MongoDB connection and document models."""
    global _db_client
    _db_client = AsyncMongoClient(MONGODB_URI)
    database = _db_client[MONGODB_DB_NAME]
    await init_beanie(
        database=database,
        document_models=[User, Resume, CoverLetter, TailoredResume, TailoredCoverLetter, ResumeTemplate, BuiltResume],
    )
    # Seed a default resume template if none exists.
    from ..db.repository import ensure_default_resume_template

    await ensure_default_resume_template()


def get_db_client() -> AsyncMongoClient | None:
    """Get MongoDB client (for advanced use). Prefer using Document models directly."""
    return _db_client


@asynccontextmanager
async def lifespan_client() -> AsyncGenerator[None, None]:
    """Lifespan context for FastAPI: init Beanie on startup, close client on shutdown."""
    await init_db()
    yield
    global _db_client
    if _db_client is not None:
        _db_client.close()
        _db_client = None
