import os

import httpx

BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")
TIMEOUT = 45.0


def _get(path: str, params: dict | None = None) -> dict | list:
    with httpx.Client(timeout=TIMEOUT) as client:
        r = client.get(f"{BASE_URL}{path}", params=params)
        r.raise_for_status()
        return r.json()


def _post(path: str, body: dict) -> dict:
    with httpx.Client(timeout=TIMEOUT) as client:
        r = client.post(f"{BASE_URL}{path}", json=body)
        r.raise_for_status()
        return r.json()


def get_patients() -> list[dict]:
    return _get("/api/v1/patients")


def get_patient_detail(patient_id: int) -> dict:
    return _get(f"/api/v1/patients/{patient_id}")


def get_patient_labs(patient_id: int, label: str | None = None) -> list[dict]:
    params = {"limit": 200}
    if label:
        params["label"] = label
    return _get(f"/api/v1/patients/{patient_id}/labs", params=params)


def get_patient_vitals(patient_id: int, label: str | None = None) -> list[dict]:
    params = {"limit": 300}
    if label:
        params["label"] = label
    return _get(f"/api/v1/patients/{patient_id}/vitals", params=params)


def post_query(patient_id: int, question: str, admission_id: int | None = None) -> dict:
    body = {"patient_id": patient_id, "question": question}
    if admission_id:
        body["admission_id"] = admission_id
    return _post("/api/v1/query", body)


def is_api_healthy() -> bool:
    try:
        with httpx.Client(timeout=3.0) as client:
            r = client.get(f"{BASE_URL}/api/v1/health")
            return r.status_code == 200
    except Exception:
        return False
