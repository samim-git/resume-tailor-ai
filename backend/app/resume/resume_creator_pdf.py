"""Generate PDF from a TailoredResume by id.

Goal: Match the frontend `ResumePreview` styling as closely as practical in PDF.
"""

from __future__ import annotations

from io import BytesIO
import re
import unicodedata
from typing import Optional

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import inch
from reportlab.pdfbase import pdfmetrics
from reportlab.platypus import Flowable, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from ..models.documents import TailoredResume
from ..models.schemas_resume import Contact, ResumeStructured, SkillCategory


MAIN_COLOR = colors.HexColor("#00BBF9")
TEXT_DARK = colors.Color(11 / 255, 18 / 255, 32 / 255, alpha=0.95)
TEXT_MUTED = colors.Color(11 / 255, 18 / 255, 32 / 255, alpha=0.7)
SEP_LIGHT = colors.Color(11 / 255, 18 / 255, 32 / 255, alpha=0.18)


def _s(v: Optional[str]) -> str:
    return (v or "").strip()

def _safe_ascii_stem(v: str) -> str:
    """
    Build an ASCII-only filename stem.
    Removes any characters that could break HTTP headers on download.
    """
    v = _s(v)
    if not v:
        return ""
    v = unicodedata.normalize("NFKD", v)
    v = v.encode("ascii", "ignore").decode("ascii")
    v = v.replace(" ", "-")
    v = re.sub(r"[^A-Za-z0-9\-_]+", "", v)
    v = re.sub(r"-{2,}", "-", v).strip("-_")
    return v


def _safe_filename(v: str, *, ext: str) -> str:
    stem = _safe_ascii_stem(v) or "resume"
    ext = ext if ext.startswith(".") else f".{ext}"
    return f"{stem[:50]}{ext}"


def _join_date(start: Optional[str], end: Optional[str]) -> str:
    start = _s(start)
    end = _s(end)
    if not start and not end:
        return ""
    if start and end:
        return f"{start} – {end}"
    return start or end


def _esc_rl(s: str) -> str:
    # Minimal escaping for ReportLab Paragraph markup.
    return (
        (s or "")
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .strip()
    )


def _contact_items(c: Contact) -> list[tuple[str, str]]:
    # De-dupe by both kind and label to avoid repeated values in the header line.
    # (e.g., if upstream parsing accidentally sets the same URL for multiple fields)
    items: list[tuple[str, str]] = []
    seen_kind: set[str] = set()
    seen_label: set[str] = set()

    def add(kind: str, label: Optional[str]) -> None:
        lab = _s(label)
        if not lab:
            return
        if kind in seen_kind:
            return
        if lab in seen_label:
            return
        seen_kind.add(kind)
        seen_label.add(lab)
        items.append((kind, lab))

    add("email", c.email)
    add("phone", c.phone)
    add("location", c.location)
    add("linkedin", c.linkedin)
    add("github", c.github)
    return items


class SectionHeader(Flowable):
    """Centered title on a dotted line (like frontend)."""

    def __init__(self, title: str, *, color=MAIN_COLOR):
        super().__init__()
        self.title = (title or "").strip().upper()
        self.color = color
        self.font_name = "Helvetica-Bold"
        self.font_size = 10.5
        self.pad_x = 10
        self.height = 18

    def wrap(self, availWidth, availHeight):  # noqa: N802
        self.width = availWidth
        return availWidth, self.height

    def draw(self):  # noqa: D401
        c = self.canv
        w = getattr(self, "width", 400)
        y = self.height / 2

        c.saveState()
        c.setStrokeColor(self.color)
        c.setLineWidth(1)
        c.setDash(1, 2)
        c.line(0, y, w, y)
        c.setDash()

        c.setFont(self.font_name, self.font_size)
        tw = pdfmetrics.stringWidth(self.title, self.font_name, self.font_size)
        box_w = tw + (self.pad_x * 2)
        box_h = self.font_size + 6
        x0 = (w - box_w) / 2
        y0 = y - box_h / 2

        # white background behind title to create "gap" in line
        c.setFillColor(colors.white)
        c.rect(x0, y0, box_w, box_h, stroke=0, fill=1)

        c.setFillColor(self.color)
        c.drawCentredString(w / 2, y0 + 3, self.title)
        c.restoreState()


class ResumeHeader(Flowable):
    """Top header: name, subtitle, centered contact line with separators."""

    def __init__(self, prof: ResumeStructured):
        super().__init__()
        self.prof = prof
        self.height = 72

    def wrap(self, availWidth, availHeight):  # noqa: N802
        self.width = availWidth
        return availWidth, self.height

    def _draw_contact_icon(self, kind: str, x: float, y: float, size: float) -> float:
        """Draw minimal vector icons; returns icon width used."""
        c = self.canv
        c.saveState()
        c.setStrokeColor(MAIN_COLOR)
        c.setFillColor(MAIN_COLOR)
        c.setLineWidth(1)

        if kind == "email":
            # envelope
            c.setFillColor(colors.white)
            c.rect(x, y, size, size * 0.72, stroke=1, fill=1)
            c.line(x, y + size * 0.72, x + size / 2, y + size * 0.36)
            c.line(x + size, y + size * 0.72, x + size / 2, y + size * 0.36)
        elif kind == "phone":
            # simple handset curve
            c.arc(x, y, x + size, y + size, startAng=220, extent=100)
            c.arc(x + size * 0.1, y + size * 0.1, x + size * 0.9, y + size * 0.9, startAng=40, extent=100)
        elif kind == "location":
            # pin: circle + drop
            c.circle(x + size / 2, y + size * 0.55, size * 0.22, stroke=1, fill=0)
            c.line(x + size / 2, y, x + size / 2, y + size * 0.33)
            c.line(x + size / 2, y, x + size * 0.2, y + size * 0.25)
            c.line(x + size / 2, y, x + size * 0.8, y + size * 0.25)
        elif kind == "linkedin":
            c.setFillColor(colors.white)
            c.rect(x, y, size, size, stroke=1, fill=1)
            c.setFillColor(MAIN_COLOR)
            c.circle(x + size * 0.3, y + size * 0.75, size * 0.07, stroke=0, fill=1)
            c.setLineWidth(1.2)
            c.line(x + size * 0.3, y + size * 0.62, x + size * 0.3, y + size * 0.2)
            c.line(x + size * 0.52, y + size * 0.55, x + size * 0.52, y + size * 0.2)
            c.line(x + size * 0.52, y + size * 0.55, x + size * 0.72, y + size * 0.55)
            c.line(x + size * 0.72, y + size * 0.55, x + size * 0.72, y + size * 0.2)
        elif kind == "github":
            # simple circle mark
            c.setFillColor(colors.white)
            c.circle(x + size / 2, y + size / 2, size * 0.48, stroke=1, fill=1)
            c.setFillColor(MAIN_COLOR)
            c.circle(x + size * 0.38, y + size * 0.6, size * 0.06, stroke=0, fill=1)
            c.circle(x + size * 0.62, y + size * 0.6, size * 0.06, stroke=0, fill=1)
            c.setLineWidth(1.1)
            c.arc(x + size * 0.34, y + size * 0.28, x + size * 0.66, y + size * 0.58, startAng=200, extent=140)

        c.restoreState()
        return size

    def draw(self):  # noqa: D401
        c = self.canv
        w = getattr(self, "width", 400)

        name = _s(self.prof.name)
        title = _s(self.prof.title)
        items = _contact_items(self.prof.contact)

        # Name
        c.saveState()
        c.setFillColor(TEXT_DARK)
        c.setFont("Helvetica-Bold", 22)
        c.drawCentredString(w / 2, self.height - 26, name or "—")

        # Subtitle (closer)
        if title:
            c.setFillColor(TEXT_MUTED)
            c.setFont("Helvetica-Bold", 10.5)
            c.drawCentredString(w / 2, self.height - 40, title)

        # Contact line
        if items:
            font_name = "Helvetica-Bold"
            font_size = 8.5
            icon = 9
            gap = 4
            sep = " | "

            c.setFont(font_name, font_size)
            text_color = TEXT_MUTED

            # compute total width to center align
            chunks: list[tuple[str, str]] = []
            for kind, label in items:
                chunks.append((kind, label))

            total = 0.0
            for i, (kind, label) in enumerate(chunks):
                total += icon + gap + pdfmetrics.stringWidth(label, font_name, font_size)
                if i != len(chunks) - 1:
                    total += pdfmetrics.stringWidth(sep, font_name, font_size)
            x = (w - total) / 2
            y = self.height - 60

            for i, (kind, label) in enumerate(chunks):
                self._draw_contact_icon(kind, x, y - 2, icon)
                x += icon + gap
                c.setFillColor(text_color)
                c.drawString(x, y, label)
                x += pdfmetrics.stringWidth(label, font_name, font_size)
                if i != len(chunks) - 1:
                    c.setFillColor(SEP_LIGHT)
                    c.drawString(x, y, sep)
                    x += pdfmetrics.stringWidth(sep, font_name, font_size)

        c.restoreState()


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


def _resume_to_flowables(prof: ResumeStructured, doc_width: float) -> list:
    """Convert ResumeStructured to ReportLab flowables."""
    parts: list = []

    body = ParagraphStyle(
        "body",
        fontName="Helvetica",
        fontSize=10,
        leading=14,
        textColor=colors.Color(11 / 255, 18 / 255, 32 / 255, alpha=0.78),
        spaceAfter=0,
        spaceBefore=0,
    )
    body_small = ParagraphStyle(
        "body_small",
        parent=body,
        fontSize=9.8,
        leading=13.8,
    )
    bold = ParagraphStyle(
        "bold",
        parent=body,
        fontName="Helvetica-Bold",
        textColor=colors.Color(11 / 255, 18 / 255, 32 / 255, alpha=0.9),
    )
    sub_bold = ParagraphStyle(
        "sub_bold",
        parent=body_small,
        fontName="Helvetica-Bold",
        textColor=colors.Color(11 / 255, 18 / 255, 32 / 255, alpha=0.82),
    )
    dates = ParagraphStyle(
        "dates",
        parent=body_small,
        fontName="Helvetica-Bold",
        textColor=colors.Color(11 / 255, 18 / 255, 32 / 255, alpha=0.6),
        alignment=2,  # right
    )
    muted = ParagraphStyle(
        "muted",
        parent=body_small,
        fontName="Helvetica-Bold",
        textColor=colors.Color(11 / 255, 18 / 255, 32 / 255, alpha=0.62),
    )

    # Header (first page only)
    parts.append(ResumeHeader(prof))
    parts.append(Spacer(1, 12))

    # Summary
    if _s(prof.professional_summary):
        parts.append(SectionHeader("Summary"))
        parts.append(Spacer(1, 6))
        parts.append(Paragraph(prof.professional_summary.replace("\n", "<br/>"), body))
        parts.append(Spacer(1, 10))

    # Skills
    if prof.skills:
        parts.append(SectionHeader("Skills"))
        parts.append(Spacer(1, 6))
        for group in prof.skills:
            if not group.skills:
                continue
            category = _s(group.category)
            skills_text = ", ".join(s for s in group.skills if _s(s))
            if category:
                parts.append(Paragraph(f"<b>{category}:</b> {skills_text}", body_small))
            else:
                parts.append(Paragraph(skills_text, body_small))
        parts.append(Spacer(1, 10))

    # Experience
    if prof.experience:
        parts.append(SectionHeader("Experience"))
        parts.append(Spacer(1, 6))
        for e in prof.experience:
            company = Paragraph(_s(e.company) or "—", bold)
            role = Paragraph(_s(e.title), sub_bold)
            date_str = _join_date(e.start_date, e.end_date)
            date_cell = Paragraph(date_str, dates) if date_str else Paragraph("", dates)

            row1 = Table([[company, ""]], colWidths=[doc_width * 0.72, doc_width * 0.28])
            row1.setStyle(TableStyle([("LEFTPADDING", (0, 0), (-1, -1), 0), ("RIGHTPADDING", (0, 0), (-1, -1), 0)]))

            row2 = Table([[role, date_cell]], colWidths=[doc_width * 0.72, doc_width * 0.28])
            row2.setStyle(
                TableStyle(
                    [
                        ("LEFTPADDING", (0, 0), (-1, -1), 0),
                        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                        ("TOPPADDING", (0, 0), (-1, -1), 0),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
                        ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ]
                )
            )

            parts.append(row1)
            parts.append(Spacer(1, 2))
            parts.append(row2)
            if _s(e.summary):
                parts.append(Paragraph(e.summary.replace("\n", "<br/>"), body))
            if e.responsibilities:
                bullets = "<br/>".join(f"• {_s(r)}" for r in e.responsibilities if _s(r))
                if bullets:
                    parts.append(Paragraph(bullets, body))
            parts.append(Spacer(1, 10))

    # Education
    if prof.education:
        parts.append(SectionHeader("Education"))
        parts.append(Spacer(1, 6))
        for ed in prof.education:
            institution = Paragraph(_s(ed.institution) or "—", bold)
            date_str = _join_date(ed.start_date, ed.end_date)
            date_cell = Paragraph(date_str, dates) if date_str else Paragraph("", dates)

            degree_field = " · ".join([p for p in [_s(ed.degree), _s(ed.field_of_study)] if p])
            field = Paragraph(degree_field, sub_bold)
            loc = Paragraph(_s(ed.location), dates) if _s(ed.location) else Paragraph("", dates)

            row1 = Table([[institution, date_cell]], colWidths=[doc_width * 0.72, doc_width * 0.28])
            row1.setStyle(
                TableStyle(
                    [
                        ("LEFTPADDING", (0, 0), (-1, -1), 0),
                        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                        ("TOPPADDING", (0, 0), (-1, -1), 0),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
                    ]
                )
            )

            row2 = Table([[field, loc]], colWidths=[doc_width * 0.72, doc_width * 0.28])
            row2.setStyle(
                TableStyle(
                    [
                        ("LEFTPADDING", (0, 0), (-1, -1), 0),
                        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                        ("TOPPADDING", (0, 0), (-1, -1), 0),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
                        ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ]
                )
            )

            parts.append(row1)
            parts.append(Spacer(1, 2))
            parts.append(row2)
            if _s(ed.notes):
                parts.append(Paragraph(ed.notes.replace("\n", "<br/>"), body))
            parts.append(Spacer(1, 10))

    # Projects
    if prof.projects:
        parts.append(SectionHeader("Projects"))
        parts.append(Spacer(1, 6))
        for p in prof.projects:
            name = Paragraph(_s(p.name) or "—", bold)
            parts.append(name)
            if _s(p.description):
                parts.append(Paragraph(p.description.replace("\n", "<br/>"), body))
            if p.technologies:
                tech = ", ".join(t for t in p.technologies if _s(t))
                if tech:
                    parts.append(Paragraph(f"<b>Tech:</b> {tech}", body_small))
            github = _s(getattr(p, "github", None))
            demo = _s(getattr(p, "demo", None) or getattr(p, "link", None))
            link_bits = []
            if github:
                link_bits.append(f'<link href="{_esc_rl(github)}">GitHub</link>')
            if demo:
                link_bits.append(f'<link href="{_esc_rl(demo)}">Demo</link>')
            if link_bits:
                parts.append(Paragraph(" | ".join(link_bits), body_small))
            parts.append(Spacer(1, 10))

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
    page = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        # Tighter margins to match the frontend "paper" look.
        leftMargin=0.35 * inch,
        rightMargin=0.35 * inch,
        topMargin=0.35 * inch,
        bottomMargin=0.4 * inch,
        title=doc.title or "Resume",
    )
    flowables = _resume_to_flowables(doc.tailored_prof, page.width)
    page.build(flowables)
    pdf_bytes = buffer.getvalue()

    filename = _safe_filename(doc.title or "resume", ext=".pdf")
    return pdf_bytes, filename


async def generate_pdf_from_current_profile(prof: ResumeStructured) -> tuple[bytes, str]:
    """
    Generate a PDF from the user's current stored profile (`User.prof`).

    Returns:
        (pdf_bytes, filename)
    """
    buffer = BytesIO()
    page = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        # Tighter margins to match the frontend "paper" look.
        leftMargin=0.35 * inch,
        rightMargin=0.35 * inch,
        topMargin=0.35 * inch,
        bottomMargin=0.4 * inch,
        title=(prof.title or "Resume"),
    )
    flowables = _resume_to_flowables(prof, page.width)
    page.build(flowables)
    pdf_bytes = buffer.getvalue()

    return pdf_bytes, _safe_filename(_s(prof.name) or _s(prof.title) or "resume", ext=".pdf")
