from pydantic import BaseModel
from typing import Any, Optional


class GenerateRequest(BaseModel):
    prompt: str
    response_schema: dict
    data: Optional[dict] = None
    model: Optional[str] = None
    system_instruction: Optional[str] = None
    temperature: float = 1.0


class GenerateResponse(BaseModel):
    result: dict
    model: str


class SkillItem(BaseModel):
    name: str
    category: str  # technical | design | soft | language | tool


class WorkExperienceItem(BaseModel):
    title: str
    company: str
    period: str
    summary: str


class EducationItem(BaseModel):
    degree: str
    institution: str
    period: str
    specialization: Optional[str] = None


class ProjectItem(BaseModel):
    name: str
    description: str
    technologies: list[str]


class ResumeData(BaseModel):
    filename: str
    profile_strength_score: int
    profile_strength_tip: str
    skills: list[SkillItem]
    work_experience: list[WorkExperienceItem]
    education: list[EducationItem]
    projects: list[ProjectItem]
    uploaded_at: str


class SkillRequired(BaseModel):
    name: str
    candidate_has: bool


class JobAnalysisResult(BaseModel):
    analysis_ready: bool
    role_summary: str
    match_reasons: list[str]
    improvement_tips: list[str]
    skills_required: list[SkillRequired]
    fit_score: int
    urgency_level: str  # high | medium | low
