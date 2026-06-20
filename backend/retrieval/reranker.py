from datetime import datetime

from backend.retrieval.types import RetrievedFact, RetrievedNote

_EPOCH = datetime(1900, 1, 1)


def rerank_facts(facts: list[RetrievedFact], entities: list[str]) -> list[RetrievedFact]:
    """
    Score each fact with additive rules, then sort descending.
    Rules are intentionally transparent — no ML, fully auditable.
    """
    entities_lower = {e.lower() for e in entities}

    for fact in facts:
        score = 0.0

        if fact.source_type == "lab":
            if fact.flag and "abnormal" in fact.flag.lower():
                score += 0.5   # abnormal results are more diagnostically relevant
            if fact.label.lower() in entities_lower:
                score += 0.3   # direct match to what the user asked about
            # Recency: latest value scores highest — use position in sorted list (handled below)

        elif fact.source_type == "medication":
            if fact.metadata.get("enddate") is None:
                score += 0.3   # active (no end date) beats historical
            if fact.label.lower() in entities_lower:
                score += 0.4   # specific drug asked about

        elif fact.source_type == "vital":
            if fact.label.lower() in entities_lower:
                score += 0.3

        elif fact.source_type == "diagnosis":
            if fact.seq_num == 1:
                score += 0.5   # primary diagnosis is most relevant
            elif fact.seq_num == 2:
                score += 0.3
            if any(e in (fact.label.lower() + " " + fact.value.lower())
                   for e in entities_lower):
                score += 0.3

        fact.relevance_score = score

    # Sort: primary key = relevance_score desc, secondary = timestamp desc
    facts.sort(
        key=lambda f: (f.relevance_score, f.timestamp or _EPOCH),
        reverse=True,
    )
    return facts


def rerank_notes(notes: list[RetrievedNote]) -> list[RetrievedNote]:
    """Score notes by category weight + BM25 score."""
    _CATEGORY_WEIGHT = {
        "discharge summary": 0.4,
        "radiology":         0.2,
        "physician":         0.15,
        "nursing":           0.05,
        "ecg":               0.1,
        "echo":              0.15,
        "consult":           0.2,
    }

    for note in notes:
        cat_weight = _CATEGORY_WEIGHT.get(note.category.lower(), 0.0)
        note.relevance_score = note.bm25_score + cat_weight

    notes.sort(key=lambda n: n.relevance_score, reverse=True)
    return notes

_EPOCH = datetime(1900, 1, 1)
