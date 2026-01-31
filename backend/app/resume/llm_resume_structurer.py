from __future__ import annotations

import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

from ..models.schemas_resume import ResumeStructured

load_dotenv()


SYSTEM_PROMPT = """You are an expert resume parser.
Extract ONLY information present in the resume text.
Do NOT invent facts. If something is missing, set it to null or [].
Return a JSON object that matches the provided schema exactly.

Normalization rules:
- Dates: prefer "YYYY-MM" if possible; else "YYYY"; if still unclear keep raw.
- experience.responsibilities: bullet points as short strings.
- skills: list of skills/technologies as individual strings (deduplicate lightly).
"""


def structure_resume_with_llm(resume_text: str) -> ResumeStructured:
    api_key = os.getenv("OPENAI_API_KEY", "")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is not set. Put it in your .env or shell profile.")

    # Choose a model you have access to. Keep it configurable.
    model = os.getenv("OPENAI_CHAT_MODEL", "gpt-4.1-mini")

    llm = ChatOpenAI(model=model, temperature=0)

    # This uses structured output (tool/function calling) so you get valid JSON.
    llm_structured = llm.with_structured_output(ResumeStructured)

    result: ResumeStructured = llm_structured.invoke(
        [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"RESUME TEXT:\n\n{resume_text}"},
        ]
    )

    return result
