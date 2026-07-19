# CareerFlow AI Service

An intelligent, lightweight microservice built with **Python**, **FastAPI**, and **Google Gemini 2.5 Pro**. This service is responsible for parsing resumes, extracting structured skills and experiences, and automatically analyzing job descriptions to provide tailored fit scores and actionable insights.

This repository operates as a standalone backend service, designed to be consumed by the main [Job Tracker Application](https://github.com/YOUR-USERNAME/job-tracker) via its Rust API gateway.

## Features

- **Resume Parsing**: Upload a PDF resume and automatically extract structured JSON data including skills, work experience, education, and projects.
- **Job URL Analysis**: Scrape LinkedIn (or other) job posting URLs and compare them against the user's parsed resume.
- **Fit Scoring & Insights**: Uses Gemini to provide a fit score (0-100), identify missing skills (gaps), summarize the role, and offer tailored tips to improve your application chances.
- **Web Search Grounding**: Integrates Google Search Grounding to automatically research hiring companies and return a comprehensive company background summary.
- **Profile Data Management**: Stores user resume data locally and allows direct overriding via API (`PUT /resume`).

## Technical Stack

- **Framework**: FastAPI (Python 3.12)
- **AI Model**: Google Gemini 2.5 Pro (`google-genai` SDK)
- **PDF Extraction**: `PyMuPDF` (fitz)
- **Deployment**: Dockerized

## Local Setup & Development

### 1. Prerequisites
- Python 3.12+
- Docker & Docker Compose (if running containerized)
- A valid **Gemini API Key**

### 2. Environment Variables
Create a `.env` file in the root directory:
```env
GEMINI_API_KEY="your_api_key_here"
```

### 3. Running Locally (Without Docker)
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
fastapi dev app/main.py --port 8001
```

The API documentation will be available at `http://localhost:8001/docs`.

### 4. Running with Docker
```bash
docker build -t ai-service .
docker run -p 8001:8001 --env-file .env ai-service
```

## API Endpoints

- `POST /resume/upload` - Uploads and parses a PDF resume.
- `GET /resume` - Retrieves the currently stored parsed resume.
- `PUT /resume` - Overwrites the currently stored parsed resume with raw JSON.
- `DELETE /resume` - Deletes the stored resume data.
- `POST /resume/parse-job-url` - Analyzes a provided job URL against the resume.
- `POST /resume/analyse-job` - Analyzes raw job description text against the resume.
