from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field


BlockType = Literal[
    "header",
    "summary",
    "skills",
    "experience",
    "education",
    "projects",
]


class TemplateTheme(BaseModel):
    """
    Theme tokens (preferred over raw CSS).
    These map cleanly to CSS variables for HTML->PDF rendering.
    """

    primary_color: str = Field(default="#00BBF9", description="Primary accent color (hex).")
    page_margin_top_mm: float = Field(default=5, description="Top page margin in mm (print).")
    page_margin_right_mm: float = Field(default=1, description="Right page margin in mm (print).")
    page_margin_bottom_mm: float = Field(default=5, description="Bottom page margin in mm (print).")
    page_margin_left_mm: float = Field(default=1, description="Left page margin in mm (print).")
    pdf_scale: float = Field(
        default=0.9,
        ge=0.5,
        le=1.2,
        description="Typography scale factor for PDF rendering. Lower = smaller fonts without shrinking the page.",
    )


class TemplateBlock(BaseModel):
    """
    A single composable block of a resume template.

    - `type`: which renderer to use.
    - `props`: block-specific config (safe, structured).
    - `style`: optional style overrides (keep small; prefer theme tokens).
    """

    type: BlockType
    props: Dict[str, Any] = Field(default_factory=dict)
    style: Dict[str, Any] = Field(default_factory=dict)


class ResumeTemplateSchema(BaseModel):
    """Portable template schema (can be stored in DB or sent via API)."""

    name: str
    version: int = 1
    is_default: bool = False
    theme: TemplateTheme = Field(default_factory=TemplateTheme)
    blocks: List[TemplateBlock] = Field(default_factory=list)

