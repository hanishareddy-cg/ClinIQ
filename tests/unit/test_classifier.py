import pytest

from backend.retrieval.classifier import QueryType, classify


@pytest.mark.parametrize("question,expected_types", [
    ("What is the patient's creatinine?",              [QueryType.LABS]),
    ("List current medications",                        [QueryType.MEDS]),
    ("What is the blood pressure?",                     [QueryType.VITALS]),
    ("Does the patient have diabetes?",                 [QueryType.DIAGNOSES]),
    ("What did the discharge summary say?",             [QueryType.NOTES]),
    ("Summarize this patient",                          [QueryType.SUMMARY]),
    ("What were the labs last 3 days?",                [QueryType.LABS, QueryType.TEMPORAL]),
    ("What is the patient's furosemide dose?",          [QueryType.MEDS]),
    ("recent potassium and sodium values",              [QueryType.LABS, QueryType.TEMPORAL]),
    ("unknown question about the patient",              [QueryType.NOTES]),  # fallback
])
def test_classify_query_type(question, expected_types):
    result = classify(question, patient_id=12345)
    for expected in expected_types:
        assert expected in result.query_type, (
            f"Expected {expected} in query_type for '{question}', got {result.query_type}"
        )


def test_classify_patient_id_preserved():
    result = classify("what are the labs?", patient_id=99999)
    assert result.patient_id == 99999


def test_classify_extracts_lab_entities():
    result = classify("what is the creatinine and potassium?", patient_id=1)
    assert "creatinine" in result.entities
    assert "potassium" in result.entities


def test_classify_extracts_time_window_days():
    result = classify("labs from the last 7 days", patient_id=1)
    assert result.time_window_days == 7


def test_classify_extracts_time_window_weeks():
    result = classify("vitals over the past 2 weeks", patient_id=1)
    assert result.time_window_days == 14


def test_classify_summary_activates_all_types():
    result = classify("summarize this patient", patient_id=1)
    assert QueryType.SUMMARY in result.query_type
    assert QueryType.LABS in result.query_type
    assert QueryType.MEDS in result.query_type
    assert QueryType.NOTES in result.query_type


def test_classify_original_preserved():
    q = "What are the patient's latest lab results?"
    result = classify(q, patient_id=1)
    assert result.original == q
