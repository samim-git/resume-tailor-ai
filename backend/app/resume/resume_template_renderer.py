from __future__ import annotations

import html
from typing import Callable, Optional

from ..models.schemas_resume import ResumeStructured
from ..models.schemas_template import TemplateBlock, TemplateTheme


def _h(v: Optional[str]) -> str:
    return html.escape((v or "").strip())


def _h_bold_markers(v: Optional[str]) -> str:
    """
    Convert \\b ... b\\ markers into <strong>...</strong>.
    Normalizes \\\\b and b\\\\ to \\b and b\\ so both single and double backslash work.
    Everything else is HTML-escaped.
    """
    s = (v or "").replace("\\\\b", "\\b").replace("b\\\\", "b\\")
    OPEN = "\\b"
    CLOSE = "b\\"
    out: list[str] = []
    i = 0
    while i < len(s):
        open_at = s.find(OPEN, i)
        if open_at == -1:
            out.append(html.escape(s[i:]))
            break
        if open_at > i:
            out.append(html.escape(s[i:open_at]))
        inner_start = open_at + len(OPEN)
        close_at = s.find(CLOSE, inner_start)
        if close_at == -1:
            out.append(html.escape(s[open_at:]))
            break
        inner = s[inner_start:close_at]
        out.append(f"<strong>{html.escape(inner)}</strong>")
        i = close_at + len(CLOSE)
    return "".join(out).strip()


def _rgba_from_hex(color: str, alpha: float) -> str:
    """
    Convert #RGB/#RRGGBB to rgba(r,g,b,a) for better print/PDF consistency.
    If the input isn't a hex color, return it as-is.
    """
    c = (color or "").strip()
    if not c.startswith("#"):
        return c
    hx = c[1:].strip()
    if len(hx) == 3:
        hx = "".join([ch * 2 for ch in hx])
    if len(hx) != 6:
        return c
    try:
        r = int(hx[0:2], 16)
        g = int(hx[2:4], 16)
        b = int(hx[4:6], 16)
        a = max(0.0, min(1.0, float(alpha)))
        return f"rgba({r}, {g}, {b}, {a})"
    except Exception:
        return c


def _join_date(start: Optional[str], end: Optional[str]) -> str:
    s = (start or "").strip()
    e = (end or "").strip()
    if not s and not e:
        return ""
    if s and e:
        return f"{s} – {e}"
    return s or e


def _contact_items(prof: ResumeStructured) -> list[tuple[str, str]]:
    c = prof.contact
    items: list[tuple[str, str]] = []
    if c.email:
        items.append(("email", c.email))
    if c.phone:
        items.append(("phone", c.phone))
    if c.location:
        items.append(("location", c.location))
    if c.linkedin:
        items.append(("linkedin", c.linkedin))
    if c.github:
        items.append(("github", c.github))

    # de-dupe by label
    seen: set[str] = set()
    out: list[tuple[str, str]] = []
    for kind, label in items:
        lab = (label or "").strip()
        if not lab or lab in seen:
            continue
        seen.add(lab)
        out.append((kind, lab))
    return out


def _fa_icon(kind: str) -> str:
    # Mirrors the frontend ResumePreview Font Awesome usage.
    if kind == "email":
        return '<i class="fa-solid fa-envelope" aria-hidden="true"></i>'
    if kind == "phone":
        return '<i class="fa-solid fa-phone" aria-hidden="true"></i>'
    if kind == "location":
        return '<i class="fa-solid fa-location-dot" aria-hidden="true"></i>'
    if kind == "linkedin":
        return '<i class="fa-brands fa-linkedin-in" aria-hidden="true"></i>'
    if kind == "github":
        return '<i class="fa-brands fa-github" aria-hidden="true"></i>'
    return ""


def _normalize_http_url(v: str) -> str:
    s = (v or "").strip()
    if not s:
        return ""
    if s.lower().startswith("http://") or s.lower().startswith("https://"):
        return s
    return f"https://{s}"


def _css(theme: TemplateTheme) -> str:
    """
    Base CSS + theme tokens. This is the source of truth for Headless Chrome PDF export.
    Keep it close to the frontend `ResumePreview.css` so output matches.
    """
    primary = (theme.primary_color or "#00BBF9").strip() or "#00BBF9"
    primary_dotted = _rgba_from_hex(primary, 0.9) or primary
    mt, mr, mb, ml = (
        theme.page_margin_top_mm,
        theme.page_margin_right_mm,
        theme.page_margin_bottom_mm,
        theme.page_margin_left_mm,
    )
    pdf_scale = getattr(theme, "pdf_scale", 1.0) or 1.0

    # Note: we intentionally avoid CSS features that can behave differently in print/PDF.
    return (
        f"""
html, body {{ margin: 0; padding: 0; background: #fff; }}
* {{ box-sizing: border-box; }}

:root {{
  font-family: system-ui, Avenir, Helvetica, Arial, sans-serif;
  line-height: 1.5;
  font-weight: 400;
  color: #0b1220;
  background-color: #ffffff;
  font-synthesis: none;
  text-rendering: optimizeLegibility;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  --primary: {primary};
  --scale: {pdf_scale};
}}

.rp {{
  width: 100%;
  max-width: 860px;
  margin: 0 auto;
  background: #fff;
  padding: calc(28px * var(--scale)) calc(34px * var(--scale));
}}

.rp__header {{ padding-bottom: 14px; border-bottom: 0; }}
.rp__headerBlock {{ text-align: center; }}
.rp__headerMain {{
  font-weight: 900; letter-spacing: -0.01em; font-size: calc(20pt * var(--scale));
  color: rgba(11, 18, 32, 0.95);
}}
.rp__headerSub {{
  margin-top: -2px; font-size: calc(11pt * var(--scale)); font-weight: 700;
  color: rgba(11, 18, 32, 0.78);
}}

.rp__contact {{
  margin-top: 10px; text-align: center; color: var(--primary);
  font-size: calc(8.8pt * var(--scale)); font-weight: 800;
}}
.rp__contactItem {{ display: inline-flex; align-items: center; gap: 6px; }}
.rp__contactIcon {{ display: inline-flex; align-items: center; justify-content: center; color: var(--primary); }}
.rp__contactText {{ color: rgba(11, 18, 32, 0.7); font-weight: 700; }}
.rp__contactLink {{ color: rgba(11, 18, 32, 0.7); font-weight: 700; text-decoration: underline; }}
.rp__contactSep {{ margin: 0 10px; color: rgba(11, 18, 32, 0.18); font-weight: 800; }}

.rp__section {{ margin-top: 1px; }}
.rp__sectionHead {{
  position: relative; display: flex; align-items: center; justify-content: center;
  margin: 16px 0 10px;
}}
.rp__sectionTitle {{
  font-weight: 900; letter-spacing: 0.06em; text-transform: uppercase;
  font-size: calc(12pt * var(--scale)); color: var(--primary); padding: 0 12px;
  background: #fff; position: relative; z-index: 1;
}}
.rp__sectionHead::before {{
  content: ''; position: absolute; left: 0; right: 0; top: 50%;
  border-top: 1px dotted {primary_dotted};
  transform: translateY(-50%);
}}

.rp__text {{
  margin-top: 6px;
  color: rgba(11, 18, 32, 0.78);
  line-height: 1.55;
  font-size: calc(10pt * var(--scale));
}}
.rp__stack {{ display: grid; gap: 12px; }}
.rp__item {{ padding: 10px 0; }}
.rp__row {{ display: flex; justify-content: space-between; gap: 10px; align-items: flex-start; }}
.rp__rowSub {{ margin-top: 2px; }}
.rp__company, .rp__school {{
  font-weight: 800; color: rgba(11, 18, 32, 0.9); font-size: calc(12pt * var(--scale));
}}
.rp__role, .rp__field {{
  font-weight: 700; color: rgba(11, 18, 32, 0.82); font-size: calc(10.5pt * var(--scale));
}}
.rp__loc {{
  color: rgba(11, 18, 32, 0.68);
  font-weight: 700;
  white-space: nowrap;
  font-size: calc(9.5pt * var(--scale));
}}
.rp__dates {{
  color: rgba(11, 18, 32, 0.6);
  font-size: calc(9pt * var(--scale));
  white-space: nowrap;
  font-weight: 600;
}}
.rp__addr {{
  color: rgba(11, 18, 32, 0.68);
  font-weight: 600;
  white-space: nowrap;
  margin-top: 4px;
  font-size: calc(9.5pt * var(--scale));
}}
.rp__muted {{ color: rgba(11, 18, 32, 0.62); font-weight: 600; }}
.rp__projLinks {{ margin-top: 6px; font-size: calc(10pt * var(--scale)); font-weight: 700; }}
.rp__link {{ color: var(--primary); text-decoration: none; }}
.rp__link:hover {{ text-decoration: underline; }}
.rp__linkSep {{ color: rgba(11, 18, 32, 0.18); font-weight: 800; }}

.rp__list {{
  margin: 8px 0 0;
  padding-left: 18px;
  color: rgba(11, 18, 32, 0.78);
  font-size: calc(10pt * var(--scale));
  line-height: 1.5;
}}

.rp__skillsBlock {{ display: grid; gap: 6px; }}
.rp__skillLine {{ color: rgba(11, 18, 32, 0.78); line-height: 1.5; }}
.rp__skillCat {{ font-weight: 800; color: rgba(11, 18, 32, 0.9); font-size: calc(11pt * var(--scale)); }}
.rp__skillCat {{ font-weight: 800; color: rgba(11, 18, 32, 0.9); font-size: calc(10.5pt * var(--scale)); }}
.rp__skillItems {{ color: rgba(11, 18, 32, 0.76); font-size: calc(10pt * var(--scale)); }}

@page {{ size: A4; margin: {mt}mm {mr}mm {mb}mm {ml}mm; }}
@media print {{
  .rp {{ max-width: none; margin: 0; }}
  body {{ -webkit-print-color-adjust: exact; print-color-adjust: exact; }}
  /* Allow long items (esp. Experience) to flow across pages */
  .rp__item {{ break-inside: auto; page-break-inside: auto; }}

  /* Keep small header rows together */
  .rp__sectionHead, .rp__row, .rp__rowSub {{ break-inside: avoid; page-break-inside: avoid; }}

  /* Prevent orphaned section headers at page bottom:
     if the next element can't fit, move header to next page. */
  .rp__sectionHead {{ break-after: avoid; page-break-after: avoid; }}
  .rp__sectionHead + * {{ break-before: avoid; page-break-before: avoid; }}

  /* Allow lists to continue, but don't split a single bullet */
  .rp__list {{ break-inside: auto; page-break-inside: auto; }}
  .rp__list li {{ break-inside: avoid; page-break-inside: avoid; }}
}}
""".strip()
    )


def _section(title: str, inner: str) -> str:
    if not inner.strip():
        return ""
    return f"""
<section class="rp__section">
  <div class="rp__sectionHead"><div class="rp__sectionTitle">{_h(title)}</div></div>
  {inner}
</section>
""".strip()


def _render_header(prof: ResumeStructured, _block: TemplateBlock) -> str:
    contact = _contact_items(prof)
    contact_html = ""
    if contact:
        items = []
        for idx, (kind, label) in enumerate(contact):
            sep = '<span class="rp__contactSep" aria-hidden="true">|</span>' if idx != len(contact) - 1 else ""
            text_html = f'<span class="rp__contactText">{_h(label)}</span>'
            if kind in {"linkedin", "github"}:
                href = _normalize_http_url(label)
                link_text = "LinkedIn" if kind == "linkedin" else "GitHub"
                if href:
                    text_html = f'<a class="rp__contactLink" href="{_h(href)}">{_h(link_text)}</a>'
            items.append(
                f"""
<span class="rp__contactItem">
  <span class="rp__contactIcon">{_fa_icon(kind)}</span>
  {text_html}
  {sep}
</span>
""".strip()
            )
        contact_html = f'<div class="rp__contact" aria-label="Contact details">{"".join(items)}</div>'

    return f"""
<header class="rp__header">
  <div class="rp__headerBlock">
    <div class="rp__headerMain">{_h(prof.name) or "—"}</div>
    {f'<div class="rp__headerSub">{_h(prof.title)}</div>' if prof.title else ""}
    {contact_html}
  </div>
</header>
""".strip()


def _render_summary(prof: ResumeStructured, _block: TemplateBlock) -> str:
    if not prof.professional_summary:
        return ""
    inner = f'<div class="rp__text">{_h(prof.professional_summary).replace("\\n", "<br/>")}</div>'
    return _section("Summary", inner)


def _render_skills(prof: ResumeStructured, _block: TemplateBlock) -> str:
    if not prof.skills:
        return ""
    rows = []
    for grp in prof.skills:
        skills = [s.strip() for s in (grp.skills or []) if (s or "").strip()]
        if not skills and not (grp.category or "").strip():
            continue
        cat = _h(grp.category) if grp.category else ""
        cat_html = f'<span class="rp__skillCat">{cat}:</span> ' if cat else ""
        rows.append(
            f'<div class="rp__skillLine">{cat_html}<span class="rp__skillItems">{_h(", ".join(skills))}</span></div>'
        )
    if not rows:
        return ""
    inner = f'<div class="rp__skillsBlock">{"".join(rows)}</div>'
    return _section("Skills", inner)


def _render_experience(prof: ResumeStructured, _block: TemplateBlock) -> str:
    if not prof.experience:
        return ""
    items: list[str] = []
    for e in prof.experience:
        company = _h(e.company) or "—"
        addr = _h(e.company_address) if getattr(e, "company_address", None) else ""
        title = _h(e.title)
        dates = _h(_join_date(e.start_date, e.end_date))

        summary_html = f'<div class="rp__text">{_h(e.summary).replace("\\n", "<br/>")}</div>' if e.summary else ""
        resp = [r.strip() for r in (e.responsibilities or []) if (r or "").strip()]
        resp_html = ""
        if resp:
            lis = "".join([f"<li>{_h_bold_markers(r)}</li>" for r in resp])
            resp_html = f'<ul class="rp__list">{lis}</ul>'

        items.append(
            f"""
<div class="rp__item">
  <div class="rp__row">
    <div class="rp__company">{company}</div>
    {f'<div class="rp__addr">{addr}</div>' if addr else ""}
  </div>
  <div class="rp__row rp__rowSub">
    <div class="rp__role">{title}</div>
    {f'<div class="rp__dates">{dates}</div>' if dates else ""}
  </div>
  {summary_html}
  {resp_html}
</div>
""".strip()
        )
    inner = f'<div class="rp__stack">{"".join(items)}</div>'
    return _section("Experience", inner)


def _render_education(prof: ResumeStructured, _block: TemplateBlock) -> str:
    if not prof.education:
        return ""
    items: list[str] = []
    for e in prof.education:
        inst = _h(e.institution) or "—"
        dates = _h(_join_date(e.start_date, e.end_date))
        field = " · ".join([p for p in [e.degree, e.field_of_study] if (p or "").strip()])
        field_h = _h(field)
        loc = _h(e.location) if e.location else ""
        notes_html = f'<div class="rp__text">{_h(e.notes).replace("\\n", "<br/>")}</div>' if e.notes else ""

        items.append(
            f"""
<div class="rp__item">
  <div class="rp__row">
    <div class="rp__school">{inst}</div>
    {f'<div class="rp__dates">{dates}</div>' if dates else ""}
  </div>
  <div class="rp__row rp__rowSub">
    <div class="rp__field">{field_h}</div>
    {f'<div class="rp__loc">{loc}</div>' if loc else ""}
  </div>
  {notes_html}
</div>
""".strip()
        )
    inner = f'<div class="rp__stack">{"".join(items)}</div>'
    return _section("Education", inner)


def _render_projects(prof: ResumeStructured, _block: TemplateBlock) -> str:
    if not prof.projects:
        return ""
    items: list[str] = []
    for p in prof.projects:
        name = _h(p.name) or "—"
        desc_html = f'<div class="rp__text">{_h(p.description).replace("\\n", "<br/>")}</div>' if p.description else ""
        tech = [t.strip() for t in (p.technologies or []) if (t or "").strip()]
        tech_html = (
            f'<div class="rp__text"><span class="rp__muted">Tech:</span> {_h(", ".join(tech))}</div>' if tech else ""
        )

        github = (getattr(p, "github", None) or "").strip()
        demo = ((getattr(p, "demo", None) or "") or (getattr(p, "link", None) or "")).strip()
        links: list[tuple[str, str]] = []
        if github:
            links.append(("GitHub", github))
        if demo:
            links.append(("Demo", demo))
        links_html = ""
        if links:
            parts = []
            for i, (label, href) in enumerate(links):
                sep = '<span class="rp__linkSep"> | </span>' if i != len(links) - 1 else ""
                parts.append(f'<a class="rp__link" href="{_h(href)}">{_h(label)}</a>{sep}')
            links_html = f'<div class="rp__projLinks">{"".join(parts)}</div>'

        items.append(
            f"""
<div class="rp__item">
  <div class="rp__company">{name}</div>
  {desc_html}
  {tech_html}
  {links_html}
</div>
""".strip()
        )
    inner = f'<div class="rp__stack">{"".join(items)}</div>'
    return _section("Projects", inner)


_RENDERERS: dict[str, Callable[[ResumeStructured, TemplateBlock], str]] = {
    "header": _render_header,
    "summary": _render_summary,
    "skills": _render_skills,
    "experience": _render_experience,
    "education": _render_education,
    "projects": _render_projects,
}


def render_resume_html(*, prof: ResumeStructured, theme: TemplateTheme, blocks: list[TemplateBlock]) -> str:
    """
    Render the resume HTML document used by Headless Chrome PDF export.
    """
    css = _css(theme)

    # External CSS for Font Awesome (mirrors frontend). If network is blocked, icons simply won't show.
    fa_link = (
        '<link rel="stylesheet" '
        'href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.2/css/all.min.css" '
        'referrerpolicy="no-referrer" />'
    )

    rendered_blocks: list[str] = []
    for b in blocks or []:
        fn = _RENDERERS.get(b.type)
        if not fn:
            continue
        rendered = fn(prof, b)
        if rendered.strip():
            rendered_blocks.append(rendered)

    body_inner = "\n".join(rendered_blocks)

    return f"""<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    {fa_link}
    <style>{css}</style>
  </head>
  <body>
    <article class="rp">
      {body_inner}
    </article>
  </body>
</html>
"""
