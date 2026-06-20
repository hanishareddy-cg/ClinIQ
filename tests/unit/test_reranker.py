from datetime import datetime

from backend.retrieval.reranker import rerank_facts, rerank_notes
from backend.retrieval.types import RetrievedFact, RetrievedNote


def _make_lab(label="Creatinine", flag=None, timestamp=None) -> RetrievedFact:
    return RetrievedFact(
        source_type="lab",
        subject_id=1,
        hadm_id=100,
        timestamp=timestamp or datetime(2112, 5, 1),
        label=label,
        value="1.0",
        unit="mg/dL",
        flag=flag,
        seq_num=None,
    )


def _make_diagnosis(seq_num=1) -> RetrievedFact:
    return RetrievedFact(
        source_type="diagnosis",
        subject_id=1,
        hadm_id=100,
        timestamp=None,
        label="Acute kidney failure",
        value="Acute renal failure, unspecified",
        unit=None,
        flag=None,
        seq_num=seq_num,
    )


def _make_note(category="Discharge summary", bm25_score=0.8) -> RetrievedNote:
    return RetrievedNote(
        doc_id="1_0",
        source_row_id=1,
        subject_id=1,
        hadm_id=100,
        chartdate="2112-05-01",
        category=category,
        highlights=["creatinine elevated"],
        bm25_score=bm25_score,
    )


def test_abnormal_lab_scores_higher_than_normal():
    normal = _make_lab(flag=None)
    abnormal = _make_lab(flag="abnormal")
    ranked = rerank_facts([normal, abnormal], entities=[])
    assert ranked[0].flag == "abnormal"


def test_entity_match_boosts_score():
    creatinine = _make_lab(label="Creatinine")
    sodium = _make_lab(label="Sodium")
    ranked = rerank_facts([sodium, creatinine], entities=["creatinine"])
    assert ranked[0].label == "Creatinine"


def test_primary_diagnosis_ranks_first():
    secondary = _make_diagnosis(seq_num=2)
    primary = _make_diagnosis(seq_num=1)
    ranked = rerank_facts([secondary, primary], entities=[])
    assert ranked[0].seq_num == 1


def test_discharge_summary_ranks_above_nursing():
    # Equal BM25 scores — category weight should be the deciding factor
    nursing = _make_note(category="Nursing", bm25_score=0.5)
    discharge = _make_note(category="Discharge summary", bm25_score=0.5)
    ranked = rerank_notes([nursing, discharge])
    assert ranked[0].category == "Discharge summary"


def test_higher_bm25_wins_within_same_category():
    low = _make_note(category="Radiology", bm25_score=0.3)
    high = _make_note(category="Radiology", bm25_score=0.9)
    ranked = rerank_notes([low, high])
    assert ranked[0].bm25_score == 0.9


def test_empty_inputs_return_empty():
    assert rerank_facts([], entities=[]) == []
    assert rerank_notes([]) == []
