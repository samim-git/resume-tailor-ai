"""Tailor a resume (ResumeStructured) for a specific job description."""

from __future__ import annotations

import os

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

from ..models.schemas_resume import ResumeStructured

load_dotenv()

TAILOR_PROMPT = """You are an expert resume tailor. Given a candidate's resume (structured) and a job description,
produce a TAILORED resume that:
1. Emphasizes relevant experience, skills, and achievements for the job
2. Uses keywords from the job description where truthful
3. Reorders/prioritizes content to match the job's requirements
4. Adapts professional summary and bullet points to be role-specific

CRITICAL: Do NOT invent experience, skills, dates, or facts. Only reframe, reorder, and rephrase what exists.
If the candidate lacks something, do not fabricate it.

Return a JSON object matching the ResumeStructured schema exactly.
"""


def tailor_resume_for_job(
    prof: ResumeStructured,
    job_description: str,
) -> ResumeStructured:
    """Tailor the candidate's profile for the given job description."""
    api_key = os.getenv("OPENAI_API_KEY", "")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is not set.")

    model = os.getenv("OPENAI_CHAT_MODEL", "gpt-4.1-mini")
    llm = ChatOpenAI(model=model, temperature=0)
    llm_structured = llm.with_structured_output(ResumeStructured)

    prof_json = prof.model_dump_json(indent=2)
    result: ResumeStructured = llm_structured.invoke(
        [
            {"role": "system", "content": TAILOR_PROMPT},
            {
                "role": "user",
                "content": f"CANDIDATE RESUME:\n\n{prof_json}\n\nJOB DESCRIPTION:\n\n{job_description}",
            },
        ]
    )
    return result
