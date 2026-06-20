# ClinIQ — Clinical Record Intelligence Platform

A clinician asking "what was this patient's creatinine trend over the last week?" should not have to open five different tabs, cross-reference lab reports, and manually piece together the answer. In most hospital systems, that's exactly what happens.

Clinical records are fragmented across structured tables (labs, vitals, medications, diagnoses) and unstructured free-text notes (discharge summaries, radiology reports, nursing assessments). Physicians spend an estimated 49% of their time on EHR documentation and data retrieval — time not spent with patients.

**ClinIQ** is a retrieval-augmented generation system that unifies both data types into a single natural language interface. Ask a question, get a precise answer with every claim cited back to the exact source record.

The system is deliberately **vectorless** — no embeddings, no vector store. PostgreSQL handles structured clinical data with typed queries; Elasticsearch BM25 handles free-text notes with term-based retrieval. This keeps the retrieval pipeline fully auditable: every retrieved fact can be traced to a row in the database or a document in the index, with no black-box similarity scores. In clinical settings, explainability is not optional.

---

## Architecture

```
User Question
     │
     ▼
┌─────────────┐
│  Classifier  │  Rule-based query type detection
│  (7 types)   │  LABS · MEDS · VITALS · DIAGNOSES · NOTES · SUMMARY · TEMPORAL
└──────┬──────┘
       │
       ├─────────────────────────────────┐
       ▼                                 ▼
┌─────────────┐                 ┌───────────────┐
│  PostgreSQL  │                 │ Elasticsearch │
│  Retriever   │                 │  BM25 Search  │
│  (async)     │                 │  (notes only) │
└──────┬──────┘                 └───────┬───────┘
       │                                │
       └────────────┬───────────────────┘
                    ▼
           ┌───────────────┐
           │    Reranker    │  Additive scoring: abnormal labs, primary dx,
           │  (rule-based)  │  discharge summaries ranked higher
           └───────┬───────┘
                   ▼
          ┌────────────────┐
          │ Context Builder │  Builds structured prompt with citation labels
          └───────┬────────┘
                  ▼
         ┌────────────────┐
         │   Groq LLM     │  Llama 3.3 70B · temperature=0.0
         │ (free tier)    │
         └───────┬────────┘
                 ▼
        Cited answer + citations
```

## Tech Stack

| Layer | Technology |
|---|---|
| Backend API | FastAPI + async SQLAlchemy |
| Structured data | PostgreSQL 16 |
| Clinical notes | Elasticsearch 8 (BM25) |
| LLM synthesis | Groq — Llama 3.3 70B (free) |
| Frontend | Streamlit |
| Containerization | Docker Compose |
| CI | GitHub Actions |

## Data

- **MIMIC-III Demo** — 100 de-identified ICU patients from [PhysioNet](https://physionet.org/content/mimiciii-demo/1.4/) (free with registration)
- **50 synthetic patients** — clinically correlated vitals, labs, and templated discharge summaries generated via script

## Features

**Query Assistant**
- Ask natural language questions about any patient
- Answers grounded entirely in retrieved records — no hallucinated facts
- Every claim cited with a bracketed source label
- Retrieval stats: latency, tokens used, facts retrieved

**Patient Explorer**
- Demographics + admission timeline
- Interactive lab trend charts
- Vital signs over time
- Full medication and diagnosis list

## Quick Start

### Prerequisites
- Docker Desktop
- Python 3.12
- A free [Groq API key](https://console.groq.com) (no credit card required)
- MIMIC-III demo files from PhysioNet (place CSVs in `data/raw/`)

### 1. Start data services

```bash
docker compose up postgres elasticsearch -d
```

### 2. Set up environment

```bash
cp .env.example .env
# Edit .env and add your GROQ_API_KEY
python -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt
```

### 3. Load data

```bash
python scripts/01_load_mimic_postgres.py    # ETL MIMIC → PostgreSQL
python scripts/02_generate_synthetic.py     # 50 synthetic patients
python scripts/03_index_notes_elasticsearch.py  # BM25 index in ES
python scripts/04_smoke_test_pipeline.py    # verify everything loaded
```

### 4. Run

```bash
# Backend
uvicorn backend.main:app --reload --port 8000

# Frontend (new terminal)
streamlit run frontend/app.py
```

Open **http://localhost:8501**

### Or run the full stack with Docker

```bash
docker compose up --build
```

## Sample Queries

| Question | Query Types Activated |
|---|---|
| What are the most recent creatinine values? | LABS |
| What medications is this patient currently on? | MEDS |
| Does this patient have a history of diabetes? | DIAGNOSES |
| What did the discharge summary say about kidney function? | NOTES |
| Summarize this patient's clinical history | SUMMARY (all types) |

## Project Structure

```
backend/
├── api/routes/        # FastAPI endpoints: /query, /patients, /health
├── retrieval/         # Classifier, PG retriever, ES retriever, reranker, context builder
├── llm/               # Groq client + prompt templates
├── models/            # SQLAlchemy ORM models + Pydantic schemas
└── es/                # Elasticsearch index setup

frontend/
├── pages/             # Query Assistant + Patient Explorer
├── components/        # Answer card with citation badges
└── utils/             # API client + formatting helpers

scripts/               # ETL: MIMIC load, synthetic generation, ES indexing, smoke test
tests/
├── unit/              # Classifier, reranker, text utils
└── integration/       # API endpoints (mocked deps, no real DB/ES needed)
```

## Tests

```bash
pytest tests/ -v
```

45 tests — unit + integration, all running without external services.

## Why Vectorless?

Most RAG demos use embeddings + a vector store. This project deliberately avoids them:

- **BM25 is more explainable** — exact term matching is auditable; cosine similarity on 1536-dimensional vectors is not
- **No embedding drift** — clinical terminology is stable; there is no need to re-embed when models change
- **Structured data belongs in SQL** — lab values, medications, and vitals are relational data, not documents
- **Strong baseline** — BM25 outperforms dense retrieval on keyword-heavy clinical text in several benchmarks

The tradeoff: semantic similarity queries ("similar symptoms") are weaker. For clinical Q&A over individual records, exact and proximity matching is the right tool.
