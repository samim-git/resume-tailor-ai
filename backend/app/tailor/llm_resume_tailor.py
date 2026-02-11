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

MANDATORY: In experience `responsibilities` bullet points, you MUST bold 2-4 important keywords/technologies per bullet.
Use the markers backslash-b and b-backslash: \\b ... b\\ (literal backslash + b to open, b + backslash to close).
Example: "Designed \\bSpring Boot RESTb\\ APIs integrated with \\bAzure Key Vaultb\\ for secrets management."
- Every responsibility bullet MUST contain at least one bolded phrase (2-4 per bullet).
- Do NOT nest markers; always close each \\b with b\\ before starting another.
- Bold job-relevant technologies, tools, and action keywords from the job description.

CRITICAL: Do NOT invent experience, skills, dates, or facts. Only reframe, reorder, and rephrase what exists.
If the candidate lacks something, do not fabricate it.

Return a JSON object matching the ResumeStructured schema exactly.
"""


def tailor_resume_for_job(
    prof: ResumeStructured,
    job_description: str,
    *,
    ai_template_message: str | None = None,
) -> ResumeStructured:
    """Tailor the candidate's profile for the given job description."""
    api_key = os.getenv("OPENAI_API_KEY", "")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is not set.")

    model = os.getenv("OPENAI_CHAT_MODEL", "gpt-4.1-mini")
    llm = ChatOpenAI(model=model, temperature=0)
    llm_structured = llm.with_structured_output(ResumeStructured)

    prof_json = prof.model_dump_json(indent=2)
    sys_prompt = TAILOR_PROMPT
    if ai_template_message and ai_template_message.strip():
        sys_prompt = (
            TAILOR_PROMPT
            + "\n\nAdditional instructions from user (apply if compatible with CRITICAL rules):\n"
            + ai_template_message.strip()
        )
    result: ResumeStructured = llm_structured.invoke(
        [
            {"role": "system", "content": sys_prompt},
            {
                "role": "user",
                "content": f"CANDIDATE RESUME:\n\n{prof_json}\n\nJOB DESCRIPTION:\n\n{job_description}",
            },
        ]
    )
    return result
