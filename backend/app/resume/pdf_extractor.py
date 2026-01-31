from __future__ import annotations

import re
from pypdf import PdfReader


def extract_text_from_pdf(pdf_path: str) -> str:
    reader = PdfReader(pdf_path)
    parts: list[str] = []

    for i, page in enumerate(reader.pages):
        text = page.extract_text() or ""
        # Basic normalization per page
        text = text.replace("\u00a0", " ")  # non-breaking space
        text = re.sub(r"[ \t]+", " ", text)
        parts.append(f"\n--- PAGE {i+1} ---\n{text.strip()}\n")

    full_text = "\n".join(parts)
    return full_text.strip()


def clean_resume_text(text: str) -> str:
    """
    Light cleanup to help LLM:
    - fix hyphen line breaks: 'develop-\nment' -> 'development'
    - collapse excessive blank lines
    - remove repeated spaces
    """
    # Fix hyphenation across line breaks
    text = re.sub(r"(\w)-\n(\w)", r"\1\2", text)

    # Normalize newlines
    text = text.replace("\r\n", "\n").replace("\r", "\n")

    # Collapse >2 newlines
    text = re.sub(r"\n{3,}", "\n\n", text)

    # Trim trailing spaces on lines
    text = "\n".join(line.rstrip() for line in text.splitlines())

    return text.strip()
