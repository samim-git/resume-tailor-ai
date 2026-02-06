from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ..auth import create_access_token, verify_password
from ..db.repository import get_user_by_username

router = APIRouter(prefix="/auth", tags=["auth"])


class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in_days: int = 7


@router.post("/login", response_model=TokenResponse, summary="Sign in")
async def login(req: LoginRequest):
    user = await get_user_by_username(req.username)
    if not user or not verify_password(req.password, user.password):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = create_access_token(subject=str(user.id))
    return TokenResponse(access_token=token)
