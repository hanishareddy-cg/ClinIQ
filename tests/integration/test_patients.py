from datetime import date

from backend.models.db_models import Admission, Diagnosis, Patient


async def test_list_patients_empty(async_client):
    response = await async_client.get("/api/v1/patients")
    assert response.status_code == 200
    assert response.json() == []


async def test_list_patients_returns_inserted(async_client, db_session):
    p = Patient(subject_id=2001, gender="F", dob=date(1985, 7, 4))
    db_session.add(p)
    await db_session.flush()

    response = await async_client.get("/api/v1/patients")
    assert response.status_code == 200
    ids = [pt["subject_id"] for pt in response.json()]
    assert 2001 in ids


async def test_get_patient_not_found(async_client):
    response = await async_client.get("/api/v1/patients/99999")
    assert response.status_code == 404


async def test_get_patient_returns_detail(async_client, db_session):
    p = Patient(subject_id=2002, gender="M", dob=date(1950, 11, 30), expire_flag=0)
    adm = Admission(hadm_id=50001, subject_id=2002, admission_type="EMERGENCY")
    dx = Diagnosis(subject_id=2002, hadm_id=50001, icd9_code="410.91", short_title="AMI", seq_num=1)
    db_session.add_all([p, adm, dx])
    await db_session.flush()

    response = await async_client.get("/api/v1/patients/2002")
    assert response.status_code == 200
    data = response.json()
    assert data["subject_id"] == 2002
    assert data["gender"] == "M"
    assert len(data["admissions"]) == 1
    assert len(data["diagnoses"]) == 1
    assert data["diagnoses"][0]["icd9_code"] == "410.91"
