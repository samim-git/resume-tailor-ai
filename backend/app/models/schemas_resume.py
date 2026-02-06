from __future__ import annotations

from typing import List, Optional
from pydantic import BaseModel, Field


class Contact(BaseModel):
    phone: Optional[str] = None
    email: Optional[str] = None
    linkedin: Optional[str] = None
    github: Optional[str] = None
    location: Optional[str] = None


class EducationItem(BaseModel):
    institution: Optional[str] = None
    degree: Optional[str] = None
    field_of_study: Optional[str] = None
    location: Optional[str] = None
    start_date: Optional[str] = Field(default=None, description="Prefer YYYY-MM or YYYY")
    end_date: Optional[str] = Field(default=None, description="Prefer YYYY-MM or YYYY")
    notes: Optional[str] = None


class ExperienceItem(BaseModel):
    title: Optional[str] = None
    company: Optional[str] = None
    company_address: Optional[str] = None
    start_date: Optional[str] = Field(default=None, description="Prefer YYYY-MM or YYYY")
    end_date: Optional[str] = Field(default=None, description="Prefer YYYY-MM or YYYY, or 'Present'")
    summary: Optional[str] = None
    responsibilities: List[str] = Field(default_factory=list)


class ProjectItem(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    technologies: List[str] = Field(default_factory=list)
    link: Optional[str] = None


class SkillCategory(BaseModel):
    category: Optional[str] = None
    skills: List[str] = Field(default_factory=list)


class ResumeStructured(BaseModel):
    name: Optional[str] = None
    title: Optional[str] = None
    contact: Contact = Field(default_factory=Contact)

    professional_summary: Optional[str] = None

    education: List[EducationItem] = Field(default_factory=list)
    experience: List[ExperienceItem] = Field(default_factory=list)
    projects: List[ProjectItem] = Field(default_factory=list)

    skills: List[SkillCategory] = Field(default_factory=list)
