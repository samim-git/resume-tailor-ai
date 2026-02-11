"""Generate a Resume PDF using Headless Chrome (Playwright).

This module is template-driven: render blocks + theme to HTML, then print to PDF.
"""

from __future__ import annotations

from ..models.schemas_resume import ResumeStructured
from ..models.schemas_template import ResumeTemplateSchema
from .resume_creator_pdf import _safe_filename  # reuse filename sanitizer
from .resume_template_renderer import render_resume_html


async def generate_pdf_with_headless_chrome(
    prof: ResumeStructured,
    *,
    template: ResumeTemplateSchema,
    filename_hint: str = "resume",
) -> tuple[bytes, str]:
    """
    Render the resume as HTML and print to PDF using Headless Chromium.

    Requirements (runtime):
      - `pip install playwright`
      - `python -m playwright install chromium`
    """
    try:
        from playwright.async_api import async_playwright  # type: ignore
    except Exception as e:  # pragma: no cover
        raise RuntimeError(
            "Playwright is not installed. Install with: pip install playwright "
            "and then: python -m playwright install chromium"
        ) from e

    html_doc = render_resume_html(prof=prof, theme=template.theme, blocks=template.blocks)

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, args=["--no-sandbox"])
        page = await browser.new_page(viewport={"width": 1200, "height": 800})
        await page.set_content(html_doc, wait_until="networkidle")
        await page.emulate_media(media="print")
        # Ensure webfonts (Font Awesome) are fully loaded before printing.
        try:
            await page.wait_for_function("document.fonts && document.fonts.status === 'loaded'", timeout=5000)
        except Exception:
            # If fonts API isn't available or times out, proceed with system fonts.
            pass
        pdf_bytes = await page.pdf(
            format="A4",
            print_background=True,
            prefer_css_page_size=True,
            margin={
                "top": f"{template.theme.page_margin_top_mm}mm",
                "right": f"{template.theme.page_margin_right_mm}mm",
                "bottom": f"{template.theme.page_margin_bottom_mm}mm",
                "left": f"{template.theme.page_margin_left_mm}mm",
            },
        )
        await browser.close()

    filename = _safe_filename(filename_hint, ext=".pdf")
    return pdf_bytes, filename

