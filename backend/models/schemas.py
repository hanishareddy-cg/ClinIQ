from datetime import datetime
from typing import Any

from pydantic import BaseModel


class QueryRequest(BaseModel):
    patient_id: int
    question: str
    admission_id: int | None = None
    max_tokens: int = 800


class Citation(BaseModel):
    id: str                   # e.g. "LAB-1", "NOTE-2"
    source_type: str          # "lab", "medication", "vital", "diagnosis", "note"
    label: str
    value: str | None = None
    unit: str | None = None
    flag: str | None = None
    timestamp: datetime | None = None
    hadm_id: int | None = None
    category: str | None = None   # for notes
    excerpt: str | None = None    # highlighted snippet for notes


class RetrievalStats(BaseModel):
    postgres_facts_retrieved: int
    es_notes_retrieved: int
    tokens_used: int
    latency_ms: int


class QueryResponse(BaseModel):
    answer: str
    citations: list[Citation]
    query_type: list[str]
    retrieval_stats: RetrievalStats
    patient_id: int


class PatientSummary(BaseModel):
    subject_id: int
    gender: str | None
    age: int | None
    alive: bool
    admission_count: int


class AdmissionDetail(BaseModel):
    hadm_id: int
    admittime: datetime | None
    dischtime: datetime | None
    admission_type: str | None
    diagnosis: str | None
    duration_days: float | None


class PatientDetail(BaseModel):
    subject_id: int
    gender: str | None
    age: int | None
    alive: bool
    admissions: list[AdmissionDetail]
    diagnoses: list[dict[str, Any]]
    medications: list[dict[str, Any]]


class HealthResponse(BaseModel):
    status: str


class ReadyResponse(BaseModel):
    postgres: bool
    elasticsearch: bool
    status: str
