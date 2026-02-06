from __future__ import annotations

import os

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import Response
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel

from ..auth import decode_token
from ..models.schemas_resume import ResumeStructured
from ..resume.llm_resume_structurer import structure_resume_with_llm
from ..resume.pdf_extractor import clean_resume_text, extract_text_from_pdf

auth_scheme = HTTPBearer()


def require_auth(credentials: HTTPAuthorizationCredentials = Depends(auth_scheme)) -> str:
    token = credentials.credentials
    try:
        payload = decode_token(token)
        return payload.get("sub", "")
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid or expired token")


router = APIRouter(prefix="/resume", tags=["resume"], dependencies=[Depends(require_auth)])

# For safety: only allow reading PDFs from this directory (configurable).
# Put your test resumes under: <project_root>/data/resumes/
BASE_RESUME_DIR = os.getenv("BASE_RESUME_DIR", os.path.abspath("docs/"))


class FormatResumeResponse(BaseModel):
    source_pdf: str
    extracted_chars: int
    resume: ResumeStructured
    saved_user_id: str | None = None


class TailorResumeRequest(BaseModel):
    job_description: str
    title: str
    job_title: str


class TailorResumeResponse(BaseModel):
    id: str
    title: str
    job_title: str
    tailored_prof: ResumeStructured


def _safe_resolve_pdf_path(pdf_path: str) -> str:
    """
    Prevent path traversal by resolving pdf_path under BASE_RESUME_DIR only.
    Accept either:
    - a filename like "myresume.pdf"
    - a relative path under BASE_RESUME_DIR like "subdir/myresume.pdf"
    """
    pdf_path = pdf_path.strip().lstrip("/")
    full_path = os.path.abspath(os.path.join(BASE_RESUME_DIR, pdf_path))

    base = os.path.abspath(BASE_RESUME_DIR)
    if not (full_path == base or full_path.startswith(base + os.sep)):
        raise HTTPException(status_code=400, detail="Invalid pdf_path (outside allowed directory).")

    if not os.path.exists(full_path):
        raise HTTPException(status_code=404, detail=f"PDF not found: {full_path}")

    if not full_path.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only .pdf files are supported.")

    return full_path


def require_auth(credentials: HTTPAuthorizationCredentials = Depends(auth_scheme)) -> str:
    token = credentials.credentials
    try:
        payload = decode_token(token)
        return payload.get("sub", "")
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid or expired token")


@router.get(
    "/format",
    response_model=FormatResumeResponse,
    summary="Extract and structure resume",
)
async def format_resume(
    pdf_path: str = Query(..., description="PDF filename or relative path under BASE_RESUME_DIR (e.g. 'resume.pdf')"),
    user_id: str = Depends(require_auth),
):
    """
    Dev endpoint: reads a local PDF from BASE_RESUME_DIR, extracts text, and structures it via LLM.
    Optionally saves extracted prof to user when user_id is provided.
    """
    from ..db.repository import save_user_prof

    full_pdf_path = _safe_resolve_pdf_path(pdf_path)
    raw_text = extract_text_from_pdf(full_pdf_path)
    cleaned_text = clean_resume_text(raw_text)

    if len(cleaned_text) < 50:
        raise HTTPException(status_code=422, detail="Extracted text too short; PDF may be scanned/image-only.")

    try:
        structured = structure_resume_with_llm(cleaned_text)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"LLM structuring failed: {str(e)}")

    try:
        await save_user_prof(user_id=user_id, prof=structured)
        saved_user_id = user_id
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save to database: {str(e)}")

    return FormatResumeResponse(
        source_pdf=os.path.basename(full_pdf_path),
        extracted_chars=len(cleaned_text),
        resume=structured,
        saved_user_id=saved_user_id,
    )


@router.post(
    "/tailor",
    response_model=TailorResumeResponse,
    summary="Tailor resume for a job",
)
async def tailor_resume(req: TailorResumeRequest, user_id: str = Depends(require_auth)):
    """
    Tailor the user's resume for a job and save to tailored_resume collection.
    Requires user to have prof set (from /resume/format with user_id).
    """
    from ..db.repository import get_user_by_id, save_tailored_resume
    from ..tailor.llm_resume_tailor import tailor_resume_for_job

    user = await get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if not user.prof:
        raise HTTPException(
            status_code=400,
            detail="User has no profile. Extract resume first via GET /resume/format?pdf_path=...&user_id=...",
        )

    try:
        tailored = tailor_resume_for_job(
            prof=user.prof,
            job_description=req.job_description,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Tailoring failed: {str(e)}")

    try:
        tailored_id = await save_tailored_resume(
            user_id=user_id,
            title=req.title,
            job_title=req.job_title,
            tailored_prof=tailored,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save: {str(e)}")

    return TailorResumeResponse(
        id=tailored_id,
        title=req.title,
        job_title=req.job_title,
        tailored_prof=tailored,
    )


@router.get(
    "/export/pdf",
    summary="Export tailored resume as PDF",
)
async def export_resume_pdf(
    tailored_resume_id: str = Query(..., description="TailoredResume id from POST /resume/tailor"),
):
    """Generate and download PDF for a tailored resume."""
    from ..resume.resume_creator_pdf import generate_pdf_from_tailored_resume

    try:
        pdf_bytes, filename = await generate_pdf_from_tailored_resume(tailored_resume_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get(
    "/export/tex",
    summary="Export tailored resume as LaTeX",
)
async def export_resume_tex(
    tailored_resume_id: str = Query(..., description="TailoredResume id from POST /resume/tailor"),
):
    """Generate and download LaTeX source (Overleaf-compatible) for a tailored resume."""
    from ..resume.resume_creator_overleaf import generate_latex_from_tailored_resume

    try:
        latex_source, filename = await generate_latex_from_tailored_resume(tailored_resume_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return Response(
        content=latex_source,
        media_type="application/x-tex",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
