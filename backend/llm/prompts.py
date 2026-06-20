from backend.retrieval.classifier import QueryType

_SYSTEM = """\
You are ClinIQ, a clinical record assistant. You answer questions about patient \
medical records with precision and always cite the specific evidence you used.

Rules:
1. Answer ONLY from the provided patient record context. Never use outside medical \
knowledge to fill gaps or make inferences not supported by the records.
2. Cite every factual claim with its source label in brackets — e.g. [LAB-1], [MED-2], [NOTE-1].
3. If the answer cannot be determined from the provided records, say exactly: \
"The available records do not contain sufficient information to answer this question."
4. For abnormal lab values, explicitly note the abnormality.
5. Present information in order of clinical relevance, not just chronological order.
6. Do not speculate about diagnoses or treatments not documented in the records.
7. Use plain language. Spell out medical abbreviations on first use.\
"""

_QUERY_USER = (
    "Patient Record Context:\n{context}\n\n"
    "Question: {question}\n\n"
    "Provide a precise, evidence-based answer with citations."
)

_SUMMARY_USER = (
    "Patient Record Context:\n{context}\n\n"
    "Provide a comprehensive clinical summary covering:\n"
    "1. Primary diagnoses and active conditions\n"
    "2. Current medications\n"
    "3. Recent lab trends (flag any abnormals)\n"
    "4. Key findings from recent clinical notes\n"
    "5. Any notable clinical events\n\n"
    "Use citations throughout."
)


def build_messages(context: str, question: str, query_type: QueryType) -> list[dict]:
    user_text = _SUMMARY_USER if QueryType.SUMMARY in query_type else _QUERY_USER
    return [
        {"role": "system", "content": _SYSTEM},
        {"role": "user", "content": user_text.format(context=context, question=question)},
    ]
