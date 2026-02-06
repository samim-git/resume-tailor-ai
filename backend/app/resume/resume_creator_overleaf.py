"""Generate LaTeX (Overleaf-compatible) code from a TailoredResume by id."""

from __future__ import annotations

from typing import Optional

from ..models.documents import TailoredResume
from ..models.schemas_resume import Contact, ResumeStructured, SkillCategory


def _escape_latex(s: Optional[str]) -> str:
    if not s:
        return ""
    replacements = {
        "&": r"\&",
        "%": r"\%",
        "$": r"\$",
        "#": r"\#",
        "_": r"\_",
        "{": r"\{",
        "}": r"\}",
        "~": r"\textasciitilde{}",
        "^": r"\textasciicircum{}",
    }
    for k, v in replacements.items():
        s = s.replace(k, v)
    return s


def _format_contact(c: Contact) -> str:
    parts = []
    if c.email:
        parts.append(c.email)
    if c.phone:
        parts.append(c.phone)
    if c.location:
        parts.append(c.location)
    if c.linkedin:
        parts.append(f"LinkedIn: {c.linkedin}")
    if c.github:
        parts.append(f"GitHub: {c.github}")
    return " $|$ ".join(_escape_latex(p) for p in parts) if parts else ""


def _format_skills(skills: list[SkillCategory]) -> str:
    lines = []
    for group in skills:
        if not group.skills:
            continue
        category = _escape_latex(group.category or "")
        skills_text = ", ".join(_escape_latex(s) for s in group.skills)
        if category:
            lines.append(r"\textbf{" + category + "}: " + skills_text)
        else:
            lines.append(skills_text)
    return r" \\ ".join(lines)


def _resume_to_latex(prof: ResumeStructured) -> str:
    """Convert ResumeStructured to LaTeX source."""
    lines = []

    # Header
    name = _escape_latex(prof.name) or ""
    title = _escape_latex(prof.title) or ""
    if name:
        lines.append(r"\begin{center}")
        lines.append(r"\textbf{\LARGE " + name + r"}")
        lines.append(r"\end{center}")
    if title:
        lines.append(r"\begin{center}" + title + r"\end{center}")
    contact_str = _format_contact(prof.contact)
    if contact_str:
        lines.append(r"\begin{center}\small " + contact_str + r"\end{center}")
    lines.append(r"\vspace{0.5cm}")

    # Professional summary
    if prof.professional_summary:
        lines.append(r"\section*{Professional Summary}")
        lines.append(_escape_latex(prof.professional_summary).replace("\n", r" \\ "))
        lines.append("")

    # Experience
    if prof.experience:
        lines.append(r"\section*{Experience}")
        for e in prof.experience:
            header = r"\textbf{" + _escape_latex(e.title or "") + r"}"
            if e.company:
                header += " --- " + _escape_latex(e.company)
            if e.start_date or e.end_date:
                header += " (" + _escape_latex(e.start_date or "") + " -- " + _escape_latex(e.end_date or "") + ")"
            lines.append(header)
            if e.summary:
                lines.append(_escape_latex(e.summary))
            if e.responsibilities:
                lines.append(r"\begin{itemize}")
                for r in e.responsibilities:
                    lines.append(r"\item " + _escape_latex(r))
                lines.append(r"\end{itemize}")
        lines.append("")

    # Education
    if prof.education:
        lines.append(r"\section*{Education}")
        for e in prof.education:
            edu = r"\textbf{" + _escape_latex(e.degree or "") + r"}"
            if e.field_of_study:
                edu += " in " + _escape_latex(e.field_of_study)
            edu += " --- " + _escape_latex(e.institution or "")
            if e.start_date or e.end_date:
                edu += " (" + _escape_latex(e.start_date or "") + " -- " + _escape_latex(e.end_date or "") + ")"
            lines.append(edu)
        lines.append("")

    # Skills
    if prof.skills:
        lines.append(r"\section*{Skills}")
        lines.append(_format_skills(prof.skills))
        lines.append("")

    # Projects
    if prof.projects:
        lines.append(r"\section*{Projects}")
        for p in prof.projects:
            lines.append(r"\textbf{" + _escape_latex(p.name or "") + r"}")
            if p.description:
                lines.append(_escape_latex(p.description))
            if p.technologies:
                lines.append("Technologies: " + ", ".join(_escape_latex(t) for t in p.technologies))
        lines.append("")

    return "\n".join(lines)


def _wrap_in_document(body: str) -> str:
    return r"""\documentclass[11pt,a4paper]{article}
\usepackage[utf8]{inputenc}
\usepackage[T1]{fontenc}
\usepackage{geometry}
\usepackage{enumitem}
\geometry{margin=1in}

\begin{document}
""" + body + r"""
\end{document}
"""


async def generate_latex_from_tailored_resume(tailored_resume_id: str) -> tuple[str, Optional[str]]:
    """
    Fetch TailoredResume by id and generate LaTeX source (Overleaf-compatible).

    Returns:
        (latex_source, filename) or raises ValueError if not found.
    """
    doc = await TailoredResume.get(tailored_resume_id)
    if not doc:
        raise ValueError(f"TailoredResume {tailored_resume_id} not found")

    body = _resume_to_latex(doc.tailored_prof)
    full_latex = _wrap_in_document(body)

    safe_title = "".join(c for c in (doc.title or "resume") if c.isalnum() or c in " -_")[:50]
    filename = f"{safe_title}.tex"
    return full_latex, filename
