"""Cover letter tailoring API."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel

from ..auth import decode_token
from ..models.documents import TailoredCoverLetter
from ..db.repository import get_user_by_id, list_tailored_cover_letters, save_tailored_cover_letter
from ..tailor.llm_cover_letter_tailor import tailor_cover_letter_for_job

auth_scheme = HTTPBearer()


def require_auth(credentials: HTTPAuthorizationCredentials = Depends(auth_scheme)) -> str:
    token = credentials.credentials
    try:
        payload = decode_token(token)
        sub = payload.get("sub", "")
        if not sub:
            raise HTTPException(status_code=401, detail="Invalid token subject")
        return sub
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid or expired token")


router = APIRouter(prefix="/cover-letter", tags=["cover-letter"])


class TailorCoverLetterRequest(BaseModel):
    title: str
    job_title: str
    job_description: str
    ai_template_message: str | None = None


class TailorCoverLetterResponse(BaseModel):
    id: str
    title: str
    job_title: str
    tailored_content: str


class TailoredCoverLetterSummary(BaseModel):
    id: str
    title: str
    job_title: str
    created_at: str
    updated_at: str


class TailoredCoverLetterListResponse(BaseModel):
    cover_letters: list[TailoredCoverLetterSummary]


class TailoredCoverLetterDetailResponse(BaseModel):
    id: str
    title: str
    job_title: str
    tailored_content: str
    created_at: str
    updated_at: str


@router.post(
    "/tailor",
    response_model=TailorCoverLetterResponse,
    summary="Generate tailored cover letter for a job",
)
async def tailor_cover_letter(req: TailorCoverLetterRequest, user_id: str = Depends(require_auth)):
    """Generate a cover letter for the job and save to tailored_cover_letter collection."""
    user = await get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if not user.prof:
        raise HTTPException(
            status_code=400,
            detail="User has no profile. Add your resume first.",
        )

    try:
        tailored_content = tailor_cover_letter_for_job(
            prof=user.prof,
            job_description=req.job_description,
            ai_template_message=req.ai_template_message,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Cover letter generation failed: {str(e)}")

    try:
        doc_id = await save_tailored_cover_letter(
            user_id=user_id,
            title=req.title,
            job_title=req.job_title,
            job_description=req.job_description,
            tailored_content=tailored_content,
            ai_template_message=req.ai_template_message,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save: {str(e)}")

    return TailorCoverLetterResponse(
        id=doc_id,
        title=req.title,
        job_title=req.job_title,
        tailored_content=tailored_content,
    )


@router.get(
    "/tailored-letters",
    response_model=TailoredCoverLetterListResponse,
    summary="List tailored cover letters (history)",
)
async def list_cover_letters(user_id: str = Depends(require_auth)):
    """List all tailored cover letters for the authenticated user."""
    docs = await list_tailored_cover_letters(user_id)
    return TailoredCoverLetterListResponse(
        cover_letters=[
            TailoredCoverLetterSummary(
                id=str(d.id),
                title=d.title,
                job_title=d.job_title,
                created_at=d.created_at.isoformat(),
                updated_at=d.updated_at.isoformat(),
            )
            for d in docs
        ]
    )


@router.get(
    "/tailored-letters/{cover_letter_id}",
    response_model=TailoredCoverLetterDetailResponse,
    summary="Get a tailored cover letter",
)
async def get_cover_letter(cover_letter_id: str, user_id: str = Depends(require_auth)):
    """Get a single tailored cover letter by id."""
    doc = await TailoredCoverLetter.get(cover_letter_id)
    if not doc or doc.user_id != user_id:
        raise HTTPException(status_code=404, detail="Cover letter not found")
    return TailoredCoverLetterDetailResponse(
        id=str(doc.id),
        title=doc.title,
        job_title=doc.job_title,
        tailored_content=doc.tailored_content,
        created_at=doc.created_at.isoformat(),
        updated_at=doc.updated_at.isoformat(),
    )
