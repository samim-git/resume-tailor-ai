# Resume Tailor Agent

An AI agent that helps users:
1) enter their job history, education, skills, and contact details  
2) paste a job description  
3) get an explainable **qualification / match score** + gap analysis  
4) generate a **tailored resume + cover letter** for that job  
5) download tailored outputs as **PDF / DOCX**, and generate **LaTeX (Overleaf)** code for easy editing

**LLM Provider:** OpenAI  
**Backend:** FastAPI  
**Agent Workflow:** LangChain + LangGraph

---

## Features

### Inputs
- User enters: job history, education, skills, summary, projects, contact details
- (Dev option) Use a **local PDF resume** → extract text → produce structured JSON

### Qualification / Match
- Parse job description into structured requirements
- Compute match score with breakdown (stable and explainable)
- Identify gaps + missing evidence

### Tailoring
- Tailored resume (ATS-friendly)
- Tailored cover letter (role-specific)
- Guardrails: **do not invent experience**

### Export
- Export tailored resume / cover letter as **PDF** and/or **DOCX**
- Generate **LaTeX** compatible with Overleaf

---

## Tech Stack

- **FastAPI** + **Uvicorn**
- **LangChain** (LLM calls, tools)
- **LangGraph** (workflow orchestration)
- **Pydantic** (strict schemas)
- **PDF text extraction:** `pypdf`
- **DOCX:** `python-docx`
- **PDF:** `reportlab` (or docx→pdf conversion later)
- **Database (recommended):** Postgres
- **Vector DB (recommended):** pgvector (inside Postgres)

---

## Suggested Project Structure

```text
.
├── backend/
│   └── app/
│       ├── main.py
│       ├── config.py
│       ├── models/
│       │   ├── __init__.py
│       │   ├── schemas_resume.py
│       │   ├── schemas_job.py
│       │   └── schemas_outputs.py
│       ├── resume/
│       │   ├── __init__.py
│       │   ├── pdf_extract.py
│       │   ├── structurer.py
│       │   └── latex_generator.py
│       ├── match/
│       │   ├── __init__.py
│       │   ├── scorer.py
│       │   └── gap_insights.py
│       ├── tailor/
│       │   ├── __init__.py
│       │   ├── resume_tailor.py
│       │   └── cover_letter_tailor.py
│       ├── export/
│       │   ├── __init__.py
│       │   ├── docx_export.py
│       │   └── pdf_export.py
│       └── agent/
│           ├── __init__.py
│           └── graph.py
├── data/
│   └── resumes/
├── .env
└── requirements.txt
```

> **Important:** Ensure each package folder contains an `__init__.py` so Python imports work.

---

## Setup

### 1) Create a virtual environment

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
```

### 2) Install dependencies

```bash
pip install fastapi "uvicorn[standard]" python-dotenv pydantic \
  langchain langgraph openai langchain-openai \
  pypdf python-docx reportlab beanie \
  sqlalchemy "psycopg[binary]" pgvector alembic
```

### 3) Create .env

Create a `.env` file in the project root:

```bash
OPENAI_API_KEY=your_key_here
OPENAI_CHAT_MODEL=gpt-4.1-mini

# Local dev folder for PDFs (only reads PDFs from here)
BASE_RESUME_DIR=./data/resumes

# MongoDB (resume-ai database)
MONGODB_URI=mongodb://admin:your_password@localhost:27017
MONGODB_DB_NAME=resume-ai

# Optional DB (later)
DATABASE_URL=postgresql+psycopg://user:pass@localhost:5432/resume_tailor
```

Verify the key is visible to Python:

```bash
python -c "import os; print('OPENAI_API_KEY set?', bool(os.getenv('OPENAI_API_KEY')))"
```

### 4) Run the API

```bash
uvicorn backend.app.main:app --reload --port 8000
```

```bash
curl http://127.0.0.1:8000/health
```

---

## Development: Local PDF → Structured Resume JSON

**1)** Put your resume PDF in `data/resumes/`:

```bash
mkdir -p data/resumes
cp /path/to/your_resume.pdf data/resumes/resume.pdf
```

**2)** Call the endpoint:

```bash
curl "http://127.0.0.1:8000/resume/format?pdf_path=resume.pdf"
```

The response typically includes:

- `source_pdf`
- `extracted_chars`
- `resume` (structured JSON)

> **Note:** This endpoint reads only from `BASE_RESUME_DIR` to avoid path traversal issues.

---

## API Overview (Target Endpoints)

### Candidate Profile

- `POST /profile` — Create/update candidate profile from form input (job history, education, skills, contact)
- `GET /profile/{id}` — Fetch profile

### Resume Structuring (Dev / Local)

- `GET /resume/format?pdf_path=resume.pdf` — Local PDF → structured resume JSON

### Job Parsing

- `POST /job/parse` — Parse job description into structured JobProfile

### Match / Qualification

- `POST /match` — Returns match score + breakdown + gaps + evidence mapping

### Tailor

- `POST /tailor/resume` — Generates a tailored resume (structured + text)
- `POST /tailor/cover-letter` — Generates a tailored cover letter

### Export

- `GET /export/resume.pdf?run_id=...`
- `GET /export/resume.docx?run_id=...`
- `GET /export/cover-letter.pdf?run_id=...`
- `GET /export/cover-letter.docx?run_id=...`

### Overleaf / LaTeX

- `GET /export/resume.tex?run_id=...` — Returns LaTeX source to paste into Overleaf

---

## Agent Workflow (LangGraph)

A controlled workflow is recommended (predictable + debuggable):

1. Parse candidate profile (or structure resume PDF/text)
2. Parse job description
3. Compute deterministic match score (Python)
4. Generate gap insights (LLM, structured output)
5. Tailor resume (ATS-friendly, evidence-based)
6. Tailor cover letter
7. Validate truthfulness (no fabricated claims)
8. Export: PDF/DOCX/LaTeX

