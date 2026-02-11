"""Generate a tailored cover letter from a candidate's resume and job description."""

from __future__ import annotations

import os

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

from ..models.schemas_resume import ResumeStructured

load_dotenv()

COVER_LETTER_PROMPT = """You are an expert cover letter writer. Given a candidate's resume (structured) and a job description,
write a compelling cover letter that:
1. Addresses the hiring manager professionally (use a generic salutation if name is unknown)
2. Highlights relevant experience and skills from the resume that match the job
3. Demonstrates enthusiasm for the role and company
4. Uses specific examples and achievements from the candidate's background
5. Ends with a strong closing and call to action

Keep the cover letter concise (typically 3-4 paragraphs). Be truthful; do NOT invent experience, skills, or facts.
Return the cover letter as plain text. Do not include markdown formatting."""


def tailor_cover_letter_for_job(
    prof: ResumeStructured,
    job_description: str,
    *,
    ai_template_message: str | None = None,
) -> str:
    """Generate a tailored cover letter for the given job description."""
    api_key = os.getenv("OPENAI_API_KEY", "")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is not set.")

    model = os.getenv("OPENAI_CHAT_MODEL", "gpt-4.1-mini")
    llm = ChatOpenAI(model=model, temperature=0.6)

    prof_json = prof.model_dump_json(indent=2)
    sys_prompt = COVER_LETTER_PROMPT
    if ai_template_message and ai_template_message.strip():
        sys_prompt = (
            COVER_LETTER_PROMPT
            + "\n\nAdditional instructions from user:\n"
            + ai_template_message.strip()
        )

    result = llm.invoke(
        [
            {"role": "system", "content": sys_prompt},
            {
                "role": "user",
                "content": f"CANDIDATE RESUME:\n\n{prof_json}\n\nJOB DESCRIPTION:\n\n{job_description}",
            },
        ]
    )
    return result.content if result.content else ""
