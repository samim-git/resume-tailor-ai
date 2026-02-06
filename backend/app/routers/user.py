from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ..auth import hash_password

router = APIRouter(prefix="/users", tags=["users"])


class CreateUserRequest(BaseModel):
    fullname: str
    username: str
    password: str


class CreateUserResponse(BaseModel):
    id: str


@router.post("/", response_model=CreateUserResponse, summary="Create a user")
async def create_user(req: CreateUserRequest):
    """Create a new user. Returns user id for use with resume extraction."""
    from ..db.repository import create_user as db_create_user

    try:
        user_id = await db_create_user(
            fullname=req.fullname,
            username=req.username,
            password=hash_password(req.password),
        )
        return CreateUserResponse(id=user_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create user: {str(e)}")
