from __future__ import annotations

import os
from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel

from .resume.pdf_extractor import extract_text_from_pdf, clean_resume_text
from .resume.llm_resume_structurer import structure_resume_with_llm
from .models.schemas_resume import ResumeStructured

app = FastAPI(title="Resume Tailor AI API", version="0.1.0")

# For safety: only allow reading PDFs from this directory (configurable).
# Put your test resumes under: <project_root>/data/resumes/
BASE_RESUME_DIR = os.getenv("BASE_RESUME_DIR", os.path.abspath("docs/"))


class FormatResumeResponse(BaseModel):
    source_pdf: str
    extracted_chars: int
    resume: ResumeStructured


def _safe_resolve_pdf_path(pdf_path: str) -> str:
    """
    Prevent path traversal by resolving pdf_path under BASE_RESUME_DIR only.
    Accept either:
    - a filename like "myresume.pdf"
    - a relative path under BASE_RESUME_DIR like "subdir/myresume.pdf"
    """
    # Normalize
    pdf_path = pdf_path.strip().lstrip("/")

    full_path = os.path.abspath(os.path.join(BASE_RESUME_DIR, pdf_path))

    # Ensure it's under BASE_RESUME_DIR
    base = os.path.abspath(BASE_RESUME_DIR)
    if not (full_path == base or full_path.startswith(base + os.sep)):
        raise HTTPException(status_code=400, detail="Invalid pdf_path (outside allowed directory).")

    if not os.path.exists(full_path):
        raise HTTPException(status_code=404, detail=f"PDF not found: {full_path}")

    if not full_path.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only .pdf files are supported.")

    return full_path


@app.get("/health")
def health():
    return {"status": "ok", "base_resume_dir": BASE_RESUME_DIR}


@app.get("/resume/format", response_model=FormatResumeResponse)
def format_resume(
    pdf_path: str = Query(..., description="PDF filename or relative path under BASE_RESUME_DIR (e.g. 'resume.pdf')")
):
    """
    Dev endpoint: reads a local PDF from BASE_RESUME_DIR, extracts text, and structures it via LLM.
    Example:
      GET /resume/format?pdf_path=resume.pdf
    """
    print(f"Formatting resume from PDF path: {pdf_path}")
    full_pdf_path = _safe_resolve_pdf_path(pdf_path)

    raw_text = extract_text_from_pdf(full_pdf_path)
    cleaned_text = clean_resume_text(raw_text)

    if len(cleaned_text) < 50:
        raise HTTPException(status_code=422, detail="Extracted text too short; PDF may be scanned/image-only.")

    # LLM structuring
    try:
        structured = structure_resume_with_llm(cleaned_text)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"LLM structuring failed: {str(e)}")

    return FormatResumeResponse(
        source_pdf=os.path.basename(full_pdf_path),
        extracted_chars=len(cleaned_text),
        resume=structured,
    )
