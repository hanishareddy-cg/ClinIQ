from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class RetrievedFact:
    source_type: str           # "lab", "medication", "vital", "diagnosis"
    subject_id: int
    hadm_id: int | None
    timestamp: datetime | None
    label: str
    value: str
    unit: str | None
    flag: str | None           # "abnormal", "delta", None
    seq_num: int | None        # for diagnoses: 1 = primary
    metadata: dict = field(default_factory=dict)
    relevance_score: float = 0.0


@dataclass
class RetrievedNote:
    doc_id: str
    source_row_id: int
    subject_id: int
    hadm_id: int | None
    chartdate: str | None
    category: str
    highlights: list[str]      # highlighted snippets from ES
    bm25_score: float
    relevance_score: float = 0.0
