from __future__ import annotations

from typing import Any, Optional

from bson import ObjectId
from pydantic import BaseModel, Field

from .schemas_resume import ResumeStructured


# Custom ObjectId type for Pydantic v2
class PyObjectId(str):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if isinstance(v, ObjectId):
            return str(v)
        if isinstance(v, str) and ObjectId.is_valid(v):
            return v
        raise ValueError("Invalid ObjectId")


class UserInDB(BaseModel):
    id: Optional[str] = Field(None, alias="_id")
    fullname: str = ""
    username: str
    password: str
    prof: Optional[ResumeStructured] = None

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}


class ResumeInDB(BaseModel):
    id: Optional[str] = Field(None, alias="_id")
    title: str
    file_link: str
    version: int = 1
    user_id: Optional[str] = None  # Link to user

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}


class CoverLetterInDB(BaseModel):
    id: Optional[str] = Field(None, alias="_id")
    title: str
    file_link: str
    version: int = 1
    user_id: Optional[str] = None  # Link to user

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}


def resume_structured_to_dict(prof: ResumeStructured) -> dict[str, Any]:
    """Convert ResumeStructured to dict for MongoDB storage."""
    return prof.model_dump()


def dict_to_resume_structured(data: dict[str, Any]) -> ResumeStructured:
    """Convert dict from MongoDB to ResumeStructured."""
    return ResumeStructured.model_validate(data)
