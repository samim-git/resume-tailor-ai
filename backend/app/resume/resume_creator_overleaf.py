"""Generate LaTeX (Overleaf-compatible) code from resume data."""

from __future__ import annotations

import re
import unicodedata
from typing import Optional

from ..models.documents import TailoredResume
from ..models.schemas_resume import Contact, ResumeStructured, SkillCategory
from ..models.schemas_template import TemplateBlock, TemplateTheme


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


def _escape_latex_with_bold_markers(s: Optional[str]) -> str:
    """
    Convert \\b ... b\\ markers into \\textbf{...} while escaping other text.
    Normalizes \\\\b and b\\\\ to \\b and b\\ so both single and double backslash work.
    """
    raw = (s or "").replace("\\\\b", "\\b").replace("b\\\\", "b\\")
    OPEN = "\\b"
    CLOSE = "b\\"
    out: list[str] = []
    i = 0
    while i < len(raw):
        open_at = raw.find(OPEN, i)
        if open_at == -1:
            out.append(_escape_latex(raw[i:]))
            break
        if open_at > i:
            out.append(_escape_latex(raw[i:open_at]))
        inner_start = open_at + len(OPEN)
        close_at = raw.find(CLOSE, inner_start)
        if close_at == -1:
            out.append(_escape_latex(raw[open_at:]))
            break
        inner = raw[inner_start:close_at]
        out.append(r"\textbf{" + _escape_latex(inner) + "}")
        i = close_at + len(CLOSE)
    return "".join(out)


def _safe_ascii_stem(v: Optional[str]) -> str:
    v = (v or "").strip()
    if not v:
        return ""
    v = unicodedata.normalize("NFKD", v)
    v = v.encode("ascii", "ignore").decode("ascii")
    v = v.replace(" ", "-")
    v = re.sub(r"[^A-Za-z0-9\-_]+", "", v)
    v = re.sub(r"-{2,}", "-", v).strip("-_")
    return v


def _join_date(start: Optional[str], end: Optional[str]) -> str:
    s = (start or "").strip()
    e = (end or "").strip()
    if not s and not e:
        return ""
    if s and e:
        return f"{s} – {e}"
    return s or e


def _format_contact(c: Contact) -> str:
    # Kept for legacy/simple generator.
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
                    lines.append(r"\item " + _escape_latex_with_bold_markers(r))
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
            # Links (GitHub / Demo)
            github = _escape_latex(getattr(p, "github", None) or "")
            demo = _escape_latex(getattr(p, "demo", None) or getattr(p, "link", None) or "")
            link_bits = []
            if github:
                link_bits.append(r"\href{" + github + r"}{GitHub}")
            if demo:
                link_bits.append(r"\href{" + demo + r"}{Demo}")
            if link_bits:
                lines.append("Links: " + " $|$ ".join(link_bits))
        lines.append("")

    return "\n".join(lines)


def _wrap_in_document(body: str) -> str:
    return r"""\documentclass[11pt,a4paper]{article}
\usepackage[utf8]{inputenc}
\usepackage[T1]{fontenc}
\usepackage{geometry}
\usepackage{enumitem}
\usepackage[hidelinks]{hyperref}
\geometry{margin=1in}

\begin{document}
""" + body + r"""
\end{document}
"""

def _hex6(v: str) -> str:
    s = (v or "").strip().lstrip("#")
    if len(s) == 3:
        s = "".join([ch * 2 for ch in s])
    if len(s) != 6:
        return "00BBF9"
    if not re.fullmatch(r"[0-9A-Fa-f]{6}", s):
        return "00BBF9"
    return s.upper()


def _normalize_http_url(v: Optional[str]) -> str:
    s = (v or "").strip()
    if not s:
        return ""
    if s.lower().startswith("http://") or s.lower().startswith("https://"):
        return s
    return f"https://{s}"


def render_latex_with_template(*, prof: ResumeStructured, theme: TemplateTheme, blocks: list[TemplateBlock]) -> str:
    """
    Template-driven LaTeX renderer intended to match ResumePreview/PDF layout closely.
    """
    primary_hex = _hex6(theme.primary_color)
    mt, mr, mb, ml = (
        theme.page_margin_top_mm,
        theme.page_margin_right_mm,
        theme.page_margin_bottom_mm,
        theme.page_margin_left_mm,
    )

    preamble = rf"""\documentclass[10pt,a4paper]{{article}}
\usepackage[utf8]{{inputenc}}
\usepackage[T1]{{fontenc}}
\usepackage{{geometry}}
\usepackage{{xcolor}}
\usepackage[hidelinks]{{hyperref}}
\usepackage{{enumitem}}
\usepackage{{tabularx}}
\usepackage{{tikz}}
\usepackage{{ragged2e}}
\usepackage{{ulem}}
\geometry{{top={mt}mm,right={mr}mm,bottom={mb}mm,left={ml}mm}}

\definecolor{{Primary}}{{HTML}}{{{primary_hex}}}

\setlength{{\parindent}}{{0pt}}
\setlength{{\parskip}}{{0pt}}
\renewcommand{{\familydefault}}{{\sfdefault}}

% Font sizes (match preview/pdf)
\newcommand{{\RPText}}[1]{{{{\fontsize{{10pt}}{{14pt}}\selectfont #1}}}}
\newcommand{{\RPContact}}[1]{{{{\fontsize{{8.8pt}}{{11pt}}\selectfont #1}}}}
\newcommand{{\RPSubTitle}}[1]{{{{\fontsize{{11pt}}{{13pt}}\selectfont #1}}}}
\newcommand{{\RPSkillCat}}[1]{{{{\fontsize{{10.5pt}}{{12.5pt}}\selectfont \textbf{{#1}}}}}}
\newcommand{{\RPSkillItems}}[1]{{{{\fontsize{{10pt}}{{12pt}}\selectfont #1}}}}
\newcommand{{\RPRole}}[1]{{{{\fontsize{{10.5pt}}{{12.5pt}}\selectfont #1}}}}
\newcommand{{\RPCompany}}[1]{{{{\fontsize{{12pt}}{{14pt}}\selectfont \textbf{{#1}}}}}}
\newcommand{{\RPAddr}}[1]{{{{\fontsize{{9.5pt}}{{11pt}}\selectfont #1}}}}
\newcommand{{\RPDates}}[1]{{{{\fontsize{{9pt}}{{11pt}}\selectfont #1}}}}
\newcommand{{\RPListText}}[1]{{{{\fontsize{{10pt}}{{12pt}}\selectfont #1}}}}

\newcommand{{\SectionHeader}}[1]{{%
  \vspace{{10pt}}%
  \begin{{center}}%
  \begin{{tikzpicture}}
    \draw[Primary, dotted, line width=0.4pt] (0,0) -- (\linewidth,0);
    \node[fill=white, inner xsep=12pt] at (0.5\linewidth,0) {{\textcolor{{Primary}}{{\fontsize{{12pt}}{{14pt}}\selectfont\bfseries\MakeUppercase{{#1}}}}}};
  \end{{tikzpicture}}%
  \end{{center}}%
  \vspace{{4pt}}%
}}

% List spacing similar to preview
\setlist[itemize]{{leftmargin=18pt, topsep=4pt, itemsep=2pt, parsep=0pt, partopsep=0pt}}

\begin{{document}}
"""

    def section(title: str, inner: str) -> str:
        inner = (inner or "").strip()
        if not inner:
            return ""
        return rf"""\SectionHeader{{{_escape_latex(title)}}}
{inner}
"""

    def render_header() -> str:
        name = _escape_latex(prof.name or "")
        title = _escape_latex(prof.title or "")
        parts: list[str] = []
        if prof.contact.email:
            parts.append(_escape_latex(prof.contact.email))
        if prof.contact.phone:
            parts.append(_escape_latex(prof.contact.phone))
        if prof.contact.location:
            parts.append(_escape_latex(prof.contact.location))
        if prof.contact.linkedin:
            url = _normalize_http_url(prof.contact.linkedin)
            parts.append(rf"\href{{{_escape_latex(url)}}}{{\uline{{LinkedIn}}}}")
        if prof.contact.github:
            url = _normalize_http_url(prof.contact.github)
            parts.append(rf"\href{{{_escape_latex(url)}}}{{\uline{{GitHub}}}}")
        contact = r" $|$ ".join(parts)

        out = []
        if name:
            out.append(r"\begin{center}" + rf"\textbf{{\fontsize{{20pt}}{{22pt}}\selectfont {name}}}" + r"\end{center}")
        if title:
            out.append(r"\begin{center}" + rf"\textcolor{{black!70}}{{\RPSubTitle{{{title}}}}}" + r"\end{center}")
        if contact:
            out.append(r"\begin{center}" + rf"\textcolor{{Primary}}{{\RPContact{{{contact}}}}}" + r"\end{center}")
        return "\n".join(out) + "\n"

    def render_summary() -> str:
        if not (prof.professional_summary or "").strip():
            return ""
        txt = _escape_latex(prof.professional_summary or "").replace("\n", r" \\ ")
        return section("Summary", rf"\RPText{{{txt}}}")

    def render_skills() -> str:
        if not prof.skills:
            return ""
        lines = []
        for grp in prof.skills:
            items = [s.strip() for s in (grp.skills or []) if (s or "").strip()]
            if not items:
                continue
            cat = _escape_latex(grp.category or "")
            items_txt = _escape_latex(", ".join(items))
            if cat:
                lines.append(rf"\RPSkillCat{{{cat}:}} \RPSkillItems{{{items_txt}}}")
            else:
                lines.append(rf"\RPSkillItems{{{items_txt}}}")
        if not lines:
            return ""
        body = r" \\ ".join(lines)
        return section("Skills", body)

    def render_experience() -> str:
        if not prof.experience:
            return ""
        chunks: list[str] = []
        for e in prof.experience:
            company = _escape_latex(e.company or "—")
            addr = _escape_latex(getattr(e, "company_address", None) or "")
            role = _escape_latex(e.title or "")
            dates = _escape_latex(_join_date(e.start_date, e.end_date))
            summary = _escape_latex(e.summary or "").replace("\n", r" \\ ")
            resp = [r.strip() for r in (e.responsibilities or []) if (r or "").strip()]

            chunks.append(
                r"\begin{tabularx}{\linewidth}{X r}"
                + rf"\RPCompany{{{company}}} & \RPAddr{{{addr}}} \\"
                + r"\end{tabularx}"
            )
            chunks.append(
                r"\begin{tabularx}{\linewidth}{X r}"
                + rf"\RPRole{{{role}}} & \RPDates{{{dates}}} \\"
                + r"\end{tabularx}"
            )
            if summary:
                chunks.append(rf"\RPText{{{summary}}}")
            if resp:
                chunks.append(r"\begin{itemize}")
                for r in resp:
                    chunks.append(rf"\item \RPListText{{{_escape_latex_with_bold_markers(r)}}}")
                chunks.append(r"\end{itemize}")
            chunks.append(r"\vspace{6pt}")
        return section("Experience", "\n".join(chunks))

    def render_education() -> str:
        if not prof.education:
            return ""
        chunks: list[str] = []
        for e in prof.education:
            inst = _escape_latex(e.institution or "—")
            dates = _escape_latex(_join_date(e.start_date, e.end_date))
            field = " · ".join([p for p in [e.degree, e.field_of_study] if (p or "").strip()])
            field_h = _escape_latex(field)
            loc = _escape_latex(e.location or "")
            notes = _escape_latex(e.notes or "").replace("\n", r" \\ ")

            chunks.append(r"\begin{tabularx}{\linewidth}{X r}" + rf"\RPCompany{{{inst}}} & \RPDates{{{dates}}} \\" + r"\end{tabularx}")
            chunks.append(r"\begin{tabularx}{\linewidth}{X r}" + rf"\RPRole{{{field_h}}} & \RPAddr{{{loc}}} \\" + r"\end{tabularx}")
            if notes:
                chunks.append(rf"\RPText{{{notes}}}")
            chunks.append(r"\vspace{6pt}")
        return section("Education", "\n".join(chunks))

    def render_projects() -> str:
        if not prof.projects:
            return ""
        chunks: list[str] = []
        for p in prof.projects:
            name = _escape_latex(p.name or "—")
            desc = _escape_latex(p.description or "").replace("\n", r" \\ ")
            tech = [t.strip() for t in (p.technologies or []) if (t or "").strip()]
            github = (getattr(p, "github", None) or "").strip()
            demo = ((getattr(p, "demo", None) or "") or (getattr(p, "link", None) or "")).strip()

            chunks.append(rf"\RPCompany{{{name}}}")
            if desc:
                chunks.append(rf"\RPText{{{desc}}}")
            if tech:
                chunks.append(rf"\RPText{{\textcolor{{black!60}}{{Tech:}} { _escape_latex(', '.join(tech)) }}}")
            link_bits: list[str] = []
            if github:
                link_bits.append(rf"\href{{{_escape_latex(_normalize_http_url(github))}}}{{\textcolor{{Primary}}{{GitHub}}}}")
            if demo:
                link_bits.append(rf"\href{{{_escape_latex(_normalize_http_url(demo))}}}{{\textcolor{{Primary}}{{Demo}}}}")
            if link_bits:
                chunks.append(r"\RPText{" + " $|$ ".join(link_bits) + "}")
            chunks.append(r"\vspace{6pt}")
        return section("Projects", "\n".join(chunks))

    renderers = {
        "header": lambda: render_header(),
        "summary": lambda: render_summary(),
        "skills": lambda: render_skills(),
        "experience": lambda: render_experience(),
        "education": lambda: render_education(),
        "projects": lambda: render_projects(),
    }

    body_chunks: list[str] = []
    for b in blocks or []:
        fn = renderers.get(b.type)
        if not fn:
            continue
        out = (fn() or "").strip()
        if out:
            body_chunks.append(out)

    body = "\n".join(body_chunks)
    return preamble + body + "\n\\end{document}\n"


def generate_latex_from_resume_structured(
    prof: ResumeStructured,
    *,
    filename_hint: str = "resume",
    theme: Optional[TemplateTheme] = None,
    blocks: Optional[list[TemplateBlock]] = None,
) -> tuple[str, str]:
    """
    Generate Overleaf-compatible LaTeX for a ResumeStructured object.
    Returns (latex_source, filename_txt).
    """
    if theme is not None and blocks is not None:
        full_latex = render_latex_with_template(prof=prof, theme=theme, blocks=blocks)
    else:
        body = _resume_to_latex(prof)
        full_latex = _wrap_in_document(body)
    safe = _safe_ascii_stem(filename_hint) or "resume"
    # User requested download as .txt
    filename = f"{safe[:50]}.tex.txt"
    return full_latex, filename


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

    safe_title = _safe_ascii_stem(doc.title or "resume") or "resume"
    filename = f"{safe_title[:50]}.tex"
    return full_latex, filename
