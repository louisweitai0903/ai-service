import io
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app.schemas import GenerateRequest, GenerateResponse
from app.gemini_client import generate_structured
from app import resume_store

RESUME_SCHEMA = {
    "type": "object",
    "properties": {
        "profile_strength_score": {"type": "integer"},
        "profile_strength_tip": {"type": "string"},
        "skills": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "category": {"type": "string", "enum": ["technical", "design", "soft", "language", "tool"]}
                },
                "required": ["name", "category"]
            }
        },
        "work_experience": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "title": {"type": "string"},
                    "company": {"type": "string"},
                    "period": {"type": "string"},
                    "summary": {"type": "string"}
                },
                "required": ["title", "company", "period", "summary"]
            }
        },
        "education": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "degree": {"type": "string"},
                    "institution": {"type": "string"},
                    "period": {"type": "string"},
                    "specialization": {"type": "string"}
                },
                "required": ["degree", "institution", "period"]
            }
        },
        "projects": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "description": {"type": "string"},
                    "technologies": {"type": "array", "items": {"type": "string"}}
                },
                "required": ["name", "description", "technologies"]
            }
        }
    },
    "required": ["profile_strength_score", "profile_strength_tip", "skills", "work_experience", "education", "projects"]
}

JOB_ANALYSIS_SCHEMA = {
    "type": "object",
    "properties": {
        "analysis_ready": {"type": "boolean"},
        "role_summary": {"type": "string"},
        "company_background": {"type": "string"},
        "match_reasons": {"type": "array", "items": {"type": "string"}},
        "improvement_tips": {"type": "array", "items": {"type": "string"}},
        "skills_required": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "candidate_has": {"type": "boolean"}
                },
                "required": ["name", "candidate_has"]
            }
        },
        "fit_score": {"type": "integer"},
        "urgency_level": {"type": "string", "enum": ["high", "medium", "low"]}
    },
    "required": ["analysis_ready", "role_summary", "company_background", "match_reasons", "improvement_tips", "skills_required", "fit_score", "urgency_level"]
}

JOB_PARSE_SCHEMA = {
    "type": "object",
    "properties": {
        "company": {"type": "string"},
        "title": {"type": "string"},
        "analysis_ready": {"type": "boolean"},
        "role_summary": {"type": "string"},
        "company_background": {"type": "string"},
        "match_reasons": {"type": "array", "items": {"type": "string"}},
        "improvement_tips": {"type": "array", "items": {"type": "string"}},
        "skills_required": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "candidate_has": {"type": "boolean"}
                },
                "required": ["name", "candidate_has"]
            }
        },
        "fit_score": {"type": "integer"},
        "urgency_level": {"type": "string", "enum": ["high", "medium", "low"]}
    },
    "required": ["company", "title", "analysis_ready", "role_summary", "company_background", "match_reasons", "improvement_tips", "skills_required", "fit_score", "urgency_level"]
}

app = FastAPI(title="CareerFlow AI Service", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health():
    return {"status": "ok", "service": "careerflow-ai"}


@app.post("/generate", response_model=GenerateResponse)
async def generate(req: GenerateRequest):
    """Generic structured Gemini call."""
    try:
        result = await generate_structured(
            prompt=req.prompt,
            response_schema=req.response_schema,
            data=req.data,
            model=req.model,
            system_instruction=req.system_instruction,
            temperature=req.temperature,
        )
        from app.config import DEFAULT_MODEL
        return GenerateResponse(result=result, model=req.model or DEFAULT_MODEL)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/resume/upload")
async def upload_resume(file: UploadFile = File(...)):
    """Upload PDF resume, parse directly using Gemini's native PDF capabilities, and persist."""
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")

    contents = await file.read()
    if len(contents) > 10 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File exceeds 10MB limit.")

    try:
        ai_result = await generate_structured(
            prompt=(
                "You are a professional resume parser. Extract all information from the attached resume file. "
                "Score profile_strength_score from 0-100 based on completeness, specificity, and measurable impact. "
                "Write profile_strength_tip as one concrete, actionable sentence to improve job match rates."
            ),
            response_schema=RESUME_SCHEMA,
            file_bytes=contents,
            mime_type="application/pdf",
            system_instruction="Extract structured data accurately from the provided resume PDF. Be thorough and specific.",
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI extraction failed: {e}")

    saved = resume_store.save_resume(file.filename, ai_result)
    return saved


@app.get("/resume")
async def get_resume():
    """Return currently stored resume data."""
    data = resume_store.load_resume()
    if not data:
        raise HTTPException(status_code=404, detail="No resume uploaded yet.")
    return data


@app.put("/resume")
async def update_resume(body: dict):
    """Manually update the stored resume data."""
    if not body:
        raise HTTPException(status_code=400, detail="Resume data required.")
    saved = resume_store.save_resume("resume.pdf", body)
    return saved


@app.delete("/resume")
async def delete_resume():
    """Clear stored resume."""
    deleted = resume_store.clear_resume()
    if not deleted:
        raise HTTPException(status_code=404, detail="No resume to delete.")
    return {"message": "Resume deleted successfully."}


@app.post("/resume/analyse-job")
async def analyse_job(body: dict):
    """Analyse a job description against the stored resume."""
    job_text = body.get("job_text", "").strip()
    if not job_text:
        raise HTTPException(status_code=400, detail="job_text is required.")

    resume = resume_store.load_resume()
    if not resume:
        raise HTTPException(status_code=404, detail="No resume found. Please upload your resume first.")

    skills_list = ", ".join(s["name"] for s in resume.get("skills", []))
    exp_list = "; ".join(
        f"{e['title']} at {e['company']} ({e['period']})" for e in resume.get("work_experience", [])
    )
    projects_list = "; ".join(p["name"] for p in resume.get("projects", []))

    try:
        result = await generate_structured(
            prompt=(
                "You are an expert career coach and talent analyst. "
                "Analyse the job description against the candidate resume profile and return a structured fit analysis. "
                "Use Google Search to find recent background information about the company and summarize it in company_background. "
                "Be specific, honest, and insightful. fit_score is 0-100. "
                "urgency_level: high=strong match pursue immediately, medium=worth applying with preparation, low=significant gaps exist."
            ),
            response_schema=JOB_ANALYSIS_SCHEMA,
            data={
                "candidate_skills": skills_list,
                "candidate_experience": exp_list,
                "candidate_projects": projects_list,
                "job_description": job_text,
            },
            system_instruction="Compare the candidate profile to the job description and produce an honest, detailed fit analysis.",
            use_google_search=True,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI analysis failed: {e}")

    return result


@app.post("/resume/parse-job-url")
async def parse_job_url(body: dict):
    """Analyse a job URL posting directly: extracts company, title, and returns full fit insights."""
    job_text = body.get("job_text", "").strip()
    if not job_text:
        raise HTTPException(status_code=400, detail="job_text is required.")

    resume = resume_store.load_resume()
    if not resume:
        raise HTTPException(status_code=404, detail="No resume found. Please upload your resume first.")

    skills_list = ", ".join(s["name"] for s in resume.get("skills", []))
    exp_list = "; ".join(
        f"{e['title']} at {e['company']} ({e['period']})" for e in resume.get("work_experience", [])
    )
    projects_list = "; ".join(p["name"] for p in resume.get("projects", []))

    try:
        result = await generate_structured(
            prompt=(
                "You are an expert career coach and talent analyst. "
                "Analyse the job description against the candidate resume profile and return a structured fit analysis. "
                "You MUST also extract the correct company name and job title from the job text. "
                "Use Google Search to find recent background information about the company and summarize it in company_background. "
                "Be specific, honest, and insightful. fit_score is 0-100. "
                "urgency_level: high=strong match pursue immediately, medium=worth applying with preparation, low=significant gaps exist."
            ),
            response_schema=JOB_PARSE_SCHEMA,
            data={
                "candidate_skills": skills_list,
                "candidate_experience": exp_list,
                "candidate_projects": projects_list,
                "job_description": job_text,
            },
            system_instruction="Compare the candidate profile to the job description and produce an honest, detailed fit analysis.",
            use_google_search=True,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI analysis failed: {e}")

    return result
