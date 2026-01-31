from typing import List, Optional
from pydantic import BaseModel, Field

class JobStructured(BaseModel):
    title: Optional[str] = None
    company: Optional[str] = None
    location: Optional[str] = None

    responsibilities: List[str] = Field(default_factory=list)
    requirements_must: List[str] = Field(default_factory=list)
    requirements_nice: List[str] = Field(default_factory=list)

    keywords: List[str] = Field(default_factory=list)
    seniority: Optional[str] = None  # e.g., junior/mid/senior/staff
