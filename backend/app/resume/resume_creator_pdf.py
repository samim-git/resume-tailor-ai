"""Generate PDF from a TailoredResume by id."""

from __future__ import annotations

from io import BytesIO
from typing import Optional

from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer

from ..models.documents import TailoredResume
from ..models.schemas_resume import Contact, ResumeStructured, SkillCategory


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
    return " | ".join(parts) if parts else ""


def _add_section(parts: list, title: str, content: str, styles: dict) -> None:
    if not content.strip():
        return
    parts.append(Paragraph(title, styles["Heading2"]))
    parts.append(Paragraph(content.replace("\n", "<br/>"), styles["Normal"]))
    parts.append(Spacer(1, 0.2 * inch))


def _format_skills(skills: list[SkillCategory]) -> str:
    lines = []
    for group in skills:
        if not group.skills:
            continue
        category = (group.category or "").strip()
        skills_text = ", ".join(group.skills)
        if category:
            lines.append(f"<b>{category}:</b> {skills_text}")
        else:
            lines.append(skills_text)
    return "<br/>".join(lines)


def _resume_to_flowables(prof: ResumeStructured, styles: dict) -> list:
    """Convert ResumeStructured to ReportLab flowables."""
    parts = []

    # Header
    name = prof.name or ""
    title = prof.title or ""
    if name:
        parts.append(Paragraph(name, styles["Heading1"]))
    if title:
        parts.append(Paragraph(title, styles["Normal"]))
    contact_str = _format_contact(prof.contact)
    if contact_str:
        parts.append(Paragraph(contact_str, styles["Normal"]))
    parts.append(Spacer(1, 0.3 * inch))

    # Professional summary
    if prof.professional_summary:
        _add_section(
            parts,
            "Professional Summary",
            prof.professional_summary,
            styles,
        )

    # Experience
    if prof.experience:
        exp_texts = []
        for e in prof.experience:
            lines = []
            header = f"<b>{e.title or ''}</b>"
            if e.company:
                header += f" — {e.company}"
            if e.start_date or e.end_date:
                header += f" ({e.start_date or ''} – {e.end_date or ''})"
            lines.append(header)
            if e.summary:
                lines.append(e.summary)
            for r in (e.responsibilities or []):
                lines.append(f"• {r}")
            exp_texts.append("<br/>".join(lines))
        _add_section(parts, "Experience", "<br/><br/>".join(exp_texts), styles)

    # Education
    if prof.education:
        edu_texts = []
        for e in prof.education:
            lines = [f"<b>{e.degree or ''}</b> in {e.field_of_study or ''} — {e.institution or ''}"]
            if e.start_date or e.end_date:
                lines.append(f"({e.start_date or ''} – {e.end_date or ''})")
            edu_texts.append("<br/>".join(lines))
        _add_section(parts, "Education", "<br/><br/>".join(edu_texts), styles)

    # Skills
    if prof.skills:
        _add_section(parts, "Skills", _format_skills(prof.skills), styles)

    # Projects
    if prof.projects:
        proj_texts = []
        for p in prof.projects:
            lines = [f"<b>{p.name or ''}</b>"]
            if p.description:
                lines.append(p.description)
            if p.technologies:
                lines.append(f"Technologies: {', '.join(p.technologies)}")
            proj_texts.append("<br/>".join(lines))
        _add_section(parts, "Projects", "<br/><br/>".join(proj_texts), styles)

    return parts


async def generate_pdf_from_tailored_resume(tailored_resume_id: str) -> tuple[bytes, Optional[str]]:
    """
    Fetch TailoredResume by id and generate PDF bytes.

    Returns:
        (pdf_bytes, filename) or raises ValueError if not found.
    """
    doc = await TailoredResume.get(tailored_resume_id)
    if not doc:
        raise ValueError(f"TailoredResume {tailored_resume_id} not found")

    buffer = BytesIO()
    page = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=0.75 * inch, leftMargin=0.75 * inch)
    styles = getSampleStyleSheet()
    flowables = _resume_to_flowables(doc.tailored_prof, styles)
    page.build(flowables)
    pdf_bytes = buffer.getvalue()

    safe_title = "".join(c for c in (doc.title or "resume") if c.isalnum() or c in " -_")[:50]
    filename = f"{safe_title}.pdf"
    return pdf_bytes, filename
