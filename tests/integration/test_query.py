from datetime import date
from unittest.mock import AsyncMock, patch

from backend.models.db_models import Patient


async def test_query_patient_not_found(async_client):
    response = await async_client.post(
        "/api/v1/query",
        json={"patient_id": 99999, "question": "What are the creatinine values?"},
    )
    assert response.status_code == 404


async def test_query_returns_answer(async_client, db_session):
    patient = Patient(subject_id=1001, gender="M", dob=date(1960, 5, 10))
    db_session.add(patient)
    await db_session.flush()

    mock_answer = "Creatinine was 2.1 mg/dL on last draw [LAB-1], which is elevated."
    with patch(
        "backend.api.routes.query.synthesize_answer",
        new=AsyncMock(return_value=(mock_answer, 120)),
    ):
        response = await async_client.post(
            "/api/v1/query",
            json={"patient_id": 1001, "question": "What are the creatinine values?"},
        )

    assert response.status_code == 200
    data = response.json()
    assert data["answer"] == mock_answer
    assert "citations" in data
    assert "query_type" in data
    assert "retrieval_stats" in data
    assert data["patient_id"] == 1001


async def test_query_summary_type_detected(async_client, db_session):
    patient = Patient(subject_id=1002, gender="F", dob=date(1975, 3, 22))
    db_session.add(patient)
    await db_session.flush()

    with patch(
        "backend.api.routes.query.synthesize_answer",
        new=AsyncMock(return_value=("Summary of clinical history.", 200)),
    ):
        response = await async_client.post(
            "/api/v1/query",
            json={"patient_id": 1002, "question": "Summarize this patient's clinical history"},
        )

    assert response.status_code == 200
    data = response.json()
    assert "SUMMARY" in data["query_type"]
