import re
from dataclasses import dataclass, field
from enum import Flag, auto


class QueryType(Flag):
    LABS      = auto()
    MEDS      = auto()
    VITALS    = auto()
    DIAGNOSES = auto()
    NOTES     = auto()
    SUMMARY   = auto()
    TEMPORAL  = auto()


@dataclass
class ClassifiedQuery:
    original: str
    query_type: QueryType
    patient_id: int
    time_window_days: int | None
    entities: list[str] = field(default_factory=list)
    normalized_query: str = ""


# --- Pattern sets (compiled once at import) ---

_LAB_TERMS = [
    "creatinine", "potassium", "sodium", "hemoglobin", "hgb", "wbc",
    "white blood cell", "platelets?", "platelet count", "lactate", "bun",
    "urea nitrogen", "inr", "troponin", "glucose", "hba1c", "hematocrit",
    "magnesium", "phosphate", "calcium", "chloride", "bicarbonate",
    "alkaline phosphatase", "alt", "ast", "bilirubin", "albumin", "lipase",
    "amylase", "pco2", "po2", "base excess",
]
_MED_TERMS = [
    "aspirin", "metformin", "lisinopril", "metoprolol", "furosemide",
    "heparin", "insulin", "warfarin", "vancomycin", "piperacillin",
    "atorvastatin", "amlodipine", "pantoprazole", "lorazepam",
]
_VITAL_TERMS = [
    "blood pressure", "heart rate", "hr", r"\bbp\b", "temperature",
    r"\btemp\b", "spo2", "oxygen saturation", "respiratory rate",
    r"\brr\b", "pulse", "o2",
]
_DIAGNOSIS_TERMS = [
    "diabetes", "hypertension", "copd", "pneumonia", "sepsis", "chf",
    "heart failure", r"\baki\b", "acute kidney", "chronic kidney",
    r"\bckd\b", "stroke", "cancer", "atrial fibrillation", r"\bafib\b",
    "myocardial infarction", r"\bmi\b", "coronary artery",
]

_P_LAB = re.compile(
    r"\b(?:lab(?:s|oratory)?|blood test|result|" + "|".join(_LAB_TERMS) + r")\b",
    re.IGNORECASE,
)
_P_MED = re.compile(
    r"\b(?:medication|medications?|drug|drugs?|prescribed?|prescription|taking|on|" + "|".join(_MED_TERMS) + r")\b",
    re.IGNORECASE,
)
_P_VITAL = re.compile(
    r"(?:" + "|".join(_VITAL_TERMS) + r")",
    re.IGNORECASE,
)
_P_DIAGNOSIS = re.compile(
    r"\b(?:diagnos(?:is|ed|es)?|condition|disease|disorder|history of|hx of|suffer|icd|" + "|".join(_DIAGNOSIS_TERMS) + r")\b",
    re.IGNORECASE,
)
_P_NOTE = re.compile(
    r"\b(?:note|notes?|wrote|said|documented|report|summary|discharge|radiology|consult|"
    r"cardiolog|nephrolog|oncolog|physician|doctor|assessment|plan)\b",
    re.IGNORECASE,
)
_P_SUMMARY = re.compile(
    r"\b(?:summar(?:ize|y|ise)|overview|tell me about|overall|full picture)\b",
    re.IGNORECASE,
)
_P_TEMPORAL = re.compile(
    r"\b(?:last|past|previous|recent|yesterday|today|trend|over time|since|history)\b"
    r"|\d+\s*(?:day|week|month|year)s?",
    re.IGNORECASE,
)
_P_TIME_WINDOW = [
    (re.compile(r"\b(\d+)\s*days?\b",   re.IGNORECASE), lambda m: int(m.group(1))),
    (re.compile(r"\b(\d+)\s*weeks?\b",  re.IGNORECASE), lambda m: int(m.group(1)) * 7),
    (re.compile(r"\b(\d+)\s*months?\b", re.IGNORECASE), lambda m: int(m.group(1)) * 30),
    (re.compile(r"\byesterday\b",       re.IGNORECASE), lambda m: 1),
    (re.compile(r"\blast\s+week\b",     re.IGNORECASE), lambda m: 7),
    (re.compile(r"\blast\s+month\b",    re.IGNORECASE), lambda m: 30),
    (re.compile(r"\blast\s+year\b",     re.IGNORECASE), lambda m: 365),
]

# Entity extractors: each returns a list of matched strings
_ENTITY_PATTERNS = [
    re.compile(r"\b(?:" + "|".join(_LAB_TERMS) + r")\b",      re.IGNORECASE),
    re.compile(r"\b(?:" + "|".join(_MED_TERMS) + r")\b",      re.IGNORECASE),
    re.compile(r"\b(?:" + "|".join(_DIAGNOSIS_TERMS) + r")\b", re.IGNORECASE),
]


def _extract_time_window(query: str) -> int | None:
    for pattern, extractor in _P_TIME_WINDOW:
        m = pattern.search(query)
        if m:
            return extractor(m)
    return None


def _extract_entities(query: str) -> list[str]:
    entities: list[str] = []
    for pattern in _ENTITY_PATTERNS:
        entities.extend(m.group(0).lower() for m in pattern.finditer(query))
    return list(dict.fromkeys(entities))  # dedupe, preserve order


def classify(question: str, patient_id: int) -> ClassifiedQuery:
    q = question.strip()
    qt = QueryType(0)

    if _P_SUMMARY.search(q):
        qt = QueryType.LABS | QueryType.MEDS | QueryType.VITALS | QueryType.DIAGNOSES | QueryType.NOTES | QueryType.SUMMARY
    else:
        if _P_LAB.search(q):
            qt |= QueryType.LABS
        if _P_MED.search(q):
            qt |= QueryType.MEDS
        if _P_VITAL.search(q):
            qt |= QueryType.VITALS
        if _P_DIAGNOSIS.search(q):
            qt |= QueryType.DIAGNOSES
        if _P_NOTE.search(q):
            qt |= QueryType.NOTES

        # Fallback: if nothing matched, search notes (free-text query)
        if not qt:
            qt = QueryType.NOTES

    if _P_TEMPORAL.search(q):
        qt |= QueryType.TEMPORAL

    return ClassifiedQuery(
        original=question,
        query_type=qt,
        patient_id=patient_id,
        time_window_days=_extract_time_window(q),
        entities=_extract_entities(q),
        normalized_query=q.lower(),
    )
