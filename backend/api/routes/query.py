import asyncio
import time

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.dependencies import get_db, get_es
from backend.llm.claude_client import synthesize_answer
from backend.models.db_models import Admission, Patient
from backend.models.schemas import QueryRequest, QueryResponse, RetrievalStats
from backend.retrieval.classifier import QueryType, classify
from backend.retrieval.context_builder import build_context
from backend.retrieval.es_retriever import search_notes
from backend.retrieval.postgres_retriever import (
    get_diagnoses,
    get_labs,
    get_medications,
    get_vitals,
)
from backend.retrieval.reranker import rerank_facts, rerank_notes

router = APIRouter()


@router.post("/query", response_model=QueryResponse)
async def query(
    request: QueryRequest,
    db: AsyncSession = Depends(get_db),
    es=Depends(get_es),
):
    start_ms = time.monotonic()

    # --- 1. Verify patient exists ---
    patient = await db.get(Patient, request.patient_id)
    if not patient:
        raise HTTPException(status_code=404, detail=f"Patient {request.patient_id} not found")

    # --- 2. Classify query ---
    cq = classify(request.question, request.patient_id)
    qt = cq.query_type

    # --- 3. Fetch admissions (needed for context header) ---
    adm_result = await db.execute(
        select(Admission)
        .where(Admission.subject_id == request.patient_id)
        .order_by(Admission.admittime.desc())
        .limit(5)
    )
    admissions = adm_result.scalars().all()
    scoped_hadm = request.admission_id

    # --- 4. PostgreSQL retrievals — run in parallel ---
    tasks = {}
    if QueryType.LABS in qt:
        lab_names = [e for e in cq.entities if _is_lab_entity(e)]
        tasks["labs"] = get_labs(db, request.patient_id, lab_names, scoped_hadm)
    if QueryType.MEDS in qt:
        med_names = [e for e in cq.entities if _is_med_entity(e)]
        tasks["meds"] = get_medications(db, request.patient_id, med_names, scoped_hadm)
    if QueryType.VITALS in qt:
        vital_names = [e for e in cq.entities if _is_vital_entity(e)]
        tasks["vitals"] = get_vitals(db, request.patient_id, vital_names, scoped_hadm)
    if QueryType.DIAGNOSES in qt:
        tasks["diagnoses"] = get_diagnoses(db, request.patient_id, cq.entities)

    pg_results = {}
    if tasks:
        gathered = await asyncio.gather(*tasks.values(), return_exceptions=True)
        for key, result in zip(tasks.keys(), gathered):
            pg_results[key] = result if not isinstance(result, Exception) else []

    all_facts = (
        pg_results.get("labs", []) +
        pg_results.get("meds", []) +
        pg_results.get("vitals", []) +
        pg_results.get("diagnoses", [])
    )

    # --- 5. Elasticsearch note retrieval ---
    es_notes = []
    if QueryType.NOTES in qt or QueryType.SUMMARY in qt:
        es_notes = await search_notes(
            es,
            subject_id=request.patient_id,
            query_text=request.question,
            hadm_id=scoped_hadm,
        )

    # --- 6. Rerank ---
    ranked_facts = rerank_facts(all_facts, cq.entities)[:15]
    ranked_notes = rerank_notes(es_notes)[:4]

    # --- 7. Build context string with citation labels ---
    context_str, citations = build_context(ranked_facts, ranked_notes, patient, list(admissions))

    # --- 8. LLM synthesis ---
    answer, tokens = await synthesize_answer(context_str, request.question, qt)

    elapsed_ms = int((time.monotonic() - start_ms) * 1000)

    return QueryResponse(
        answer=answer,
        citations=citations,
        query_type=[f.name for f in QueryType if f in qt and f != QueryType.TEMPORAL],
        retrieval_stats=RetrievalStats(
            postgres_facts_retrieved=len(all_facts),
            es_notes_retrieved=len(es_notes),
            tokens_used=tokens,
            latency_ms=elapsed_ms,
        ),
        patient_id=request.patient_id,
    )


# --- Entity type helpers (used to route extracted entities to the right retriever) ---

_LAB_KEYWORDS = {
    "creatinine", "potassium", "sodium", "hemoglobin", "hgb", "wbc",
    "white blood cell", "platelets", "platelet count", "lactate", "bun",
    "urea nitrogen", "inr", "troponin", "glucose", "hba1c", "hematocrit",
    "magnesium", "phosphate", "calcium", "chloride", "alt", "ast",
    "bilirubin", "albumin", "lipase", "amylase",
}
_MED_KEYWORDS = {
    "aspirin", "metformin", "lisinopril", "metoprolol", "furosemide",
    "heparin", "insulin", "warfarin", "vancomycin", "piperacillin",
    "atorvastatin", "amlodipine", "pantoprazole",
}
_VITAL_KEYWORDS = {
    "blood pressure", "heart rate", "hr", "bp", "temperature", "temp",
    "spo2", "oxygen", "respiratory rate", "rr", "pulse",
}


def _is_lab_entity(e: str) -> bool:
    return any(k in e for k in _LAB_KEYWORDS)


def _is_med_entity(e: str) -> bool:
    return any(k in e for k in _MED_KEYWORDS)


def _is_vital_entity(e: str) -> bool:
    return any(k in e for k in _VITAL_KEYWORDS)
