from __future__ import annotations

import os

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import Response
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel

from ..auth import decode_token
from ..models.schemas_resume import ResumeStructured
from ..models.schemas_template import ResumeTemplateSchema, TemplateBlock, TemplateTheme
from ..resume.llm_resume_structurer import structure_resume_with_llm
from ..resume.pdf_extractor import clean_resume_text, extract_text_from_pdf

auth_scheme = HTTPBearer()

def _content_disposition_attachment(filename: str) -> str:
    """
    Starlette encodes headers as latin-1, so filename must be ASCII-safe.
    We also add RFC 5987 filename* for better client support.
    """
    from urllib.parse import quote

    ascii_name = (filename or "resume").encode("ascii", "ignore").decode("ascii") or "resume.pdf"
    ascii_name = ascii_name.replace('"', "")
    return f"attachment; filename=\"{ascii_name}\"; filename*=UTF-8''{quote(filename or ascii_name)}"


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


router = APIRouter(prefix="/resume", tags=["resume"], dependencies=[Depends(require_auth)])

# For safety: only allow reading PDFs from this directory (configurable).
# Put your test resumes under: <project_root>/data/resumes/
BASE_RESUME_DIR = os.getenv("BASE_RESUME_DIR", os.path.abspath("docs/"))


class FormatResumeResponse(BaseModel):
    source_pdf: str
    extracted_chars: int
    resume: ResumeStructured
    saved_user_id: str | None = None


class CurrentResumeResponse(BaseModel):
    resume: ResumeStructured | None = None


class TailorResumeRequest(BaseModel):
    job_description: str
    title: str
    job_title: str
    ai_template_message: str | None = None


class TailorResumeResponse(BaseModel):
    id: str
    title: str
    job_title: str
    tailored_prof: ResumeStructured


class TailoredResumeSummary(BaseModel):
    id: str
    title: str
    job_title: str
    created_at: str
    updated_at: str


class TailoredResumeListResponse(BaseModel):
    resumes: list[TailoredResumeSummary]


class TailoredResumeDetailResponse(BaseModel):
    id: str
    title: str
    job_title: str
    tailored_prof: ResumeStructured
    created_at: str
    updated_at: str


class ResumeTemplateSummary(BaseModel):
    id: str
    name: str
    version: int
    is_default: bool
    created_at: str
    updated_at: str


class ResumeTemplateListResponse(BaseModel):
    templates: list[ResumeTemplateSummary]


class CreateResumeTemplateRequest(BaseModel):
    name: str
    version: int = 1
    is_default: bool = False
    theme: TemplateTheme = TemplateTheme()
    blocks: list[TemplateBlock] = []


class UpdateResumeTemplateRequest(BaseModel):
    name: str
    version: int = 1
    is_default: bool = False
    theme: TemplateTheme = TemplateTheme()
    blocks: list[TemplateBlock] = []


class ResumeTemplateResponse(BaseModel):
    id: str
    template: ResumeTemplateSchema


class BuiltResumeSummary(BaseModel):
    id: str
    title: str
    created_at: str
    updated_at: str


class BuiltResumeListResponse(BaseModel):
    resumes: list[BuiltResumeSummary]


class CreateBuiltResumeRequest(BaseModel):
    title: str | None = None
    source: str = "blank"  # "blank" | "current"
    template_id: str | None = None


class BuiltResumeResponse(BaseModel):
    id: str
    title: str
    resume: ResumeStructured
    template_id: str | None = None
    created_at: str
    updated_at: str


class UpdateBuiltResumeRequest(BaseModel):
    title: str
    resume: ResumeStructured
    template_id: str | None = None


def _template_doc_to_schema(doc) -> ResumeTemplateSchema:
    return ResumeTemplateSchema(
        name=doc.name,
        version=doc.version,
        is_default=doc.is_default,
        theme=doc.theme,
        blocks=doc.blocks,
    )


def _template_doc_to_summary(doc) -> ResumeTemplateSummary:
    # stringify datetimes for clean JSON / TS friendliness
    return ResumeTemplateSummary(
        id=str(doc.id),
        name=doc.name,
        version=doc.version,
        is_default=doc.is_default,
        created_at=doc.created_at.isoformat(),
        updated_at=doc.updated_at.isoformat(),
    )


def _built_doc_to_summary(doc) -> BuiltResumeSummary:
    return BuiltResumeSummary(
        id=str(doc.id),
        title=doc.title,
        created_at=doc.created_at.isoformat(),
        updated_at=doc.updated_at.isoformat(),
    )


def _built_doc_to_response(doc) -> BuiltResumeResponse:
    return BuiltResumeResponse(
        id=str(doc.id),
        title=doc.title,
        resume=doc.resume,
        template_id=getattr(doc, "template_id", None),
        created_at=doc.created_at.isoformat(),
        updated_at=doc.updated_at.isoformat(),
    )


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


@router.get(
    "/current",
    response_model=CurrentResumeResponse,
    summary="Get current resume profile",
)
async def get_current_resume(user_id: str = Depends(require_auth)):
    """
    Returns the current user's stored resume profile (prof) from the database.
    """
    from ..db.repository import get_user_by_id

    user = await get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return CurrentResumeResponse(resume=user.prof)


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
            ai_template_message=req.ai_template_message,
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
    template_id: str | None = Query(None, description="Resume template id (optional). Uses default when omitted."),
    user_id: str = Depends(require_auth),
):
    """Generate and download PDF for a tailored resume."""
    from ..db.repository import get_default_resume_template, get_resume_template_by_id
    from ..models.documents import TailoredResume
    from ..models.schemas_template import ResumeTemplateSchema
    from ..resume.resume_creator_chrome_pdf import generate_pdf_with_headless_chrome

    doc = await TailoredResume.get(tailored_resume_id)
    if not doc or doc.user_id != user_id:
        raise HTTPException(status_code=404, detail="Tailored resume not found")

    if template_id:
        tpl_doc = await get_resume_template_by_id(template_id)
        if not tpl_doc:
            raise HTTPException(status_code=404, detail="Resume template not found")
    else:
        tpl_doc = await get_default_resume_template()

    template = ResumeTemplateSchema(
        name=tpl_doc.name,
        version=tpl_doc.version,
        is_default=tpl_doc.is_default,
        theme=tpl_doc.theme,
        blocks=tpl_doc.blocks,
    )

    pdf_bytes, filename = await generate_pdf_with_headless_chrome(
        doc.tailored_prof,
        template=template,
        filename_hint=(doc.title or doc.job_title or "resume"),
    )
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": _content_disposition_attachment(filename or "resume.pdf")},
    )


@router.get(
    "/export/current/pdf",
    summary="Export current resume profile as PDF",
)
async def export_current_resume_pdf(
    template_id: str | None = Query(None, description="Resume template id (optional). Uses default when omitted."),
    user_id: str = Depends(require_auth),
):
    """
    Generate and download a PDF for the currently authenticated user's stored profile (`User.prof`).
    """
    from ..db.repository import get_user_by_id
    from ..db.repository import get_default_resume_template, get_resume_template_by_id
    from ..models.schemas_template import ResumeTemplateSchema
    from ..resume.resume_creator_chrome_pdf import generate_pdf_with_headless_chrome

    user = await get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if not user.prof:
        raise HTTPException(status_code=404, detail="User has no resume profile (prof) yet")

    if template_id:
        tpl_doc = await get_resume_template_by_id(template_id)
        if not tpl_doc:
            raise HTTPException(status_code=404, detail="Resume template not found")
    else:
        tpl_doc = await get_default_resume_template()

    template = ResumeTemplateSchema(
        name=tpl_doc.name,
        version=tpl_doc.version,
        is_default=tpl_doc.is_default,
        theme=tpl_doc.theme,
        blocks=tpl_doc.blocks,
    )

    pdf_bytes, filename = await generate_pdf_with_headless_chrome(
        user.prof,
        template=template,
        filename_hint=(user.fullname or user.username or "resume"),
    )
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": _content_disposition_attachment(filename or "resume.pdf")},
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
        headers={"Content-Disposition": _content_disposition_attachment(filename or "resume.tex")},
    )


@router.get(
    "/templates",
    response_model=ResumeTemplateListResponse,
    summary="List resume templates",
)
async def list_resume_templates():
    from ..models.documents import ResumeTemplate

    docs = await ResumeTemplate.find_all().sort("-updated_at").to_list()
    return ResumeTemplateListResponse(templates=[_template_doc_to_summary(d) for d in docs])


@router.get(
    "/templates/{template_id}",
    response_model=ResumeTemplateResponse,
    summary="Get a resume template",
)
async def get_resume_template(template_id: str):
    from ..models.documents import ResumeTemplate

    doc = await ResumeTemplate.get(template_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Resume template not found")
    return ResumeTemplateResponse(id=str(doc.id), template=_template_doc_to_schema(doc))


@router.post(
    "/templates",
    response_model=ResumeTemplateResponse,
    summary="Create a resume template",
)
async def create_resume_template(req: CreateResumeTemplateRequest):
    from ..models.documents import ResumeTemplate

    if req.is_default:
        # unset any existing default first
        existing_defaults = await ResumeTemplate.find(ResumeTemplate.is_default == True).to_list()  # noqa: E712
        for d in existing_defaults:
            d.is_default = False
            await d.save()

    doc = ResumeTemplate(
        name=req.name,
        version=req.version,
        is_default=req.is_default,
        theme=req.theme,
        blocks=req.blocks,
    )
    await doc.insert()
    return ResumeTemplateResponse(id=str(doc.id), template=_template_doc_to_schema(doc))


@router.put(
    "/templates/{template_id}",
    response_model=ResumeTemplateResponse,
    summary="Update a resume template",
)
async def update_resume_template(template_id: str, req: UpdateResumeTemplateRequest):
    from ..models.documents import ResumeTemplate

    doc = await ResumeTemplate.get(template_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Resume template not found")

    if req.is_default:
        existing_defaults = await ResumeTemplate.find(ResumeTemplate.is_default == True).to_list()  # noqa: E712
        for d in existing_defaults:
            if str(d.id) == str(doc.id):
                continue
            d.is_default = False
            await d.save()

    doc.name = req.name
    doc.version = req.version
    doc.is_default = req.is_default
    doc.theme = req.theme
    doc.blocks = req.blocks
    await doc.save()

    return ResumeTemplateResponse(id=str(doc.id), template=_template_doc_to_schema(doc))


@router.post(
    "/templates/{template_id}/duplicate",
    response_model=ResumeTemplateResponse,
    summary="Duplicate a resume template",
)
async def duplicate_resume_template(template_id: str):
    from ..models.documents import ResumeTemplate

    doc = await ResumeTemplate.get(template_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Resume template not found")

    copy = ResumeTemplate(
        name=f"{doc.name} (copy)",
        version=doc.version,
        is_default=False,
        theme=doc.theme,
        blocks=doc.blocks,
    )
    await copy.insert()
    return ResumeTemplateResponse(id=str(copy.id), template=_template_doc_to_schema(copy))


@router.get(
    "/built-resumes",
    response_model=BuiltResumeListResponse,
    summary="List built resumes",
)
async def list_built_resumes(user_id: str = Depends(require_auth)):
    from ..models.documents import BuiltResume

    docs = await BuiltResume.find(BuiltResume.user_id == user_id).sort("-updated_at").to_list()
    return BuiltResumeListResponse(resumes=[_built_doc_to_summary(d) for d in docs])


@router.post(
    "/built-resumes",
    response_model=BuiltResumeResponse,
    summary="Create a built resume (blank or from current profile)",
)
async def create_built_resume(req: CreateBuiltResumeRequest, user_id: str = Depends(require_auth)):
    from ..db.repository import get_user_by_id
    from ..models.documents import BuiltResume
    from ..models.schemas_resume import Contact

    title = (req.title or "").strip() or "Untitled"
    source = (req.source or "blank").strip().lower()
    template_id = (req.template_id or "").strip() or None
    if template_id == "default":
        template_id = None

    if source not in {"blank", "current"}:
        raise HTTPException(status_code=422, detail="Invalid source. Use 'blank' or 'current'.")

    if source == "current":
        user = await get_user_by_id(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        if not user.prof:
            raise HTTPException(status_code=404, detail="User has no resume profile (prof) yet")
        resume = user.prof
    else:
        resume = ResumeStructured(
            name="",
            title="",
            contact=Contact(),
            professional_summary="",
            education=[],
            experience=[],
            projects=[],
            skills=[],
        )

    doc = BuiltResume(user_id=user_id, title=title, resume=resume, template_id=template_id)
    await doc.insert()
    return _built_doc_to_response(doc)


@router.get(
    "/built-resumes/{built_resume_id}",
    response_model=BuiltResumeResponse,
    summary="Get a built resume",
)
async def get_built_resume(built_resume_id: str, user_id: str = Depends(require_auth)):
    from ..models.documents import BuiltResume

    doc = await BuiltResume.get(built_resume_id)
    if not doc or doc.user_id != user_id:
        raise HTTPException(status_code=404, detail="Built resume not found")
    return _built_doc_to_response(doc)


@router.put(
    "/built-resumes/{built_resume_id}",
    response_model=BuiltResumeResponse,
    summary="Update (save) a built resume",
)
async def update_built_resume(built_resume_id: str, req: UpdateBuiltResumeRequest, user_id: str = Depends(require_auth)):
    from ..models.documents import BuiltResume

    doc = await BuiltResume.get(built_resume_id)
    if not doc or doc.user_id != user_id:
        raise HTTPException(status_code=404, detail="Built resume not found")

    doc.title = (req.title or "").strip() or "Untitled"
    doc.resume = req.resume
    template_id = (req.template_id or "").strip() or None
    if template_id == "default":
        template_id = None
    doc.template_id = template_id
    await doc.save()
    return _built_doc_to_response(doc)


@router.get(
    "/built-resumes/{built_resume_id}/export/pdf",
    summary="Export a built resume as PDF",
)
async def export_built_resume_pdf(
    built_resume_id: str,
    template_id: str | None = Query(None, description="Resume template id (optional). Uses default when omitted."),
    user_id: str = Depends(require_auth),
):
    from ..db.repository import get_default_resume_template, get_resume_template_by_id
    from ..models.documents import BuiltResume
    from ..models.schemas_template import ResumeTemplateSchema
    from ..resume.resume_creator_chrome_pdf import generate_pdf_with_headless_chrome

    doc = await BuiltResume.get(built_resume_id)
    if not doc or doc.user_id != user_id:
        raise HTTPException(status_code=404, detail="Built resume not found")

    effective_template_id = template_id or getattr(doc, "template_id", None) or None
    if effective_template_id:
        if effective_template_id == "default":
            effective_template_id = None

    if effective_template_id:
        tpl_doc = await get_resume_template_by_id(effective_template_id)
        if not tpl_doc:
            raise HTTPException(status_code=404, detail="Resume template not found")
    else:
        tpl_doc = await get_default_resume_template()

    template = ResumeTemplateSchema(
        name=tpl_doc.name,
        version=tpl_doc.version,
        is_default=tpl_doc.is_default,
        theme=tpl_doc.theme,
        blocks=tpl_doc.blocks,
    )

    pdf_bytes, filename = await generate_pdf_with_headless_chrome(
        doc.resume,
        template=template,
        filename_hint=(doc.title or "resume"),
    )
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": _content_disposition_attachment(filename or "resume.pdf")},
    )


@router.get(
    "/built-resumes/{built_resume_id}/export/tex",
    summary="Export a built resume as LaTeX (as .txt)",
)
async def export_built_resume_tex(
    built_resume_id: str,
    template_id: str | None = Query(None, description="Resume template id (optional). Uses default when omitted."),
    user_id: str = Depends(require_auth),
):
    from ..models.documents import BuiltResume
    from ..db.repository import get_default_resume_template, get_resume_template_by_id
    from ..resume.resume_creator_overleaf import generate_latex_from_resume_structured

    doc = await BuiltResume.get(built_resume_id)
    if not doc or doc.user_id != user_id:
        raise HTTPException(status_code=404, detail="Built resume not found")

    effective_template_id = template_id or getattr(doc, "template_id", None) or None
    if effective_template_id and effective_template_id == "default":
        effective_template_id = None

    if effective_template_id:
        tpl_doc = await get_resume_template_by_id(effective_template_id)
        if not tpl_doc:
            raise HTTPException(status_code=404, detail="Resume template not found")
    else:
        tpl_doc = await get_default_resume_template()

    latex_source, filename = generate_latex_from_resume_structured(
        doc.resume,
        filename_hint=(doc.title or "resume"),
        theme=tpl_doc.theme,
        blocks=tpl_doc.blocks,
    )
    return Response(
        content=latex_source,
        media_type="text/plain; charset=utf-8",
        headers={"Content-Disposition": _content_disposition_attachment(filename or "resume.tex.txt")},
    )


@router.get(
    "/tailored-resumes",
    response_model=TailoredResumeListResponse,
    summary="List tailored resumes (history)",
)
async def list_tailored_resumes(user_id: str = Depends(require_auth)):
    from ..models.documents import TailoredResume

    docs = await TailoredResume.find(TailoredResume.user_id == user_id).sort("-updated_at").to_list()
    return TailoredResumeListResponse(
        resumes=[
            TailoredResumeSummary(
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
    "/tailored-resumes/{tailored_resume_id}",
    response_model=TailoredResumeDetailResponse,
    summary="Get a tailored resume",
)
async def get_tailored_resume(tailored_resume_id: str, user_id: str = Depends(require_auth)):
    from ..models.documents import TailoredResume

    doc = await TailoredResume.get(tailored_resume_id)
    if not doc or doc.user_id != user_id:
        raise HTTPException(status_code=404, detail="Tailored resume not found")

    return TailoredResumeDetailResponse(
        id=str(doc.id),
        title=doc.title,
        job_title=doc.job_title,
        tailored_prof=doc.tailored_prof,
        created_at=doc.created_at.isoformat(),
        updated_at=doc.updated_at.isoformat(),
    )
