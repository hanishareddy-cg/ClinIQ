from datetime import date

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.dependencies import get_db
from backend.models.db_models import Admission, Diagnosis, LabResult, Medication, Patient, Vital
from backend.models.schemas import AdmissionDetail, PatientDetail, PatientSummary

router = APIRouter()


def _compute_age(dob: date | None, dod: date | None) -> int | None:
    if dob is None:
        return None
    end = dod or date.today()
    age = end.year - dob.year - ((end.month, end.day) < (dob.month, dob.day))
    # MIMIC shifts DOBs by 300 years for patients >89 — cap at 89
    return min(age, 89)


@router.get("/patients", response_model=list[PatientSummary])
async def list_patients(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(
            Patient,
            func.count(Admission.hadm_id).label("admission_count"),
        )
        .outerjoin(Admission, Admission.subject_id == Patient.subject_id)
        .group_by(Patient.subject_id)
        .order_by(Patient.subject_id)
    )
    rows = result.all()
    return [
        PatientSummary(
            subject_id=p.subject_id,
            gender=p.gender,
            age=_compute_age(p.dob, p.dod),
            alive=p.expire_flag != 1,
            admission_count=count,
        )
        for p, count in rows
    ]


@router.get("/patients/{patient_id}", response_model=PatientDetail)
async def get_patient(patient_id: int, db: AsyncSession = Depends(get_db)):
    patient = await db.get(Patient, patient_id)
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    admissions_result = await db.execute(
        select(Admission)
        .where(Admission.subject_id == patient_id)
        .order_by(Admission.admittime.desc())
    )
    admissions = admissions_result.scalars().all()

    diagnoses_result = await db.execute(
        select(Diagnosis)
        .where(Diagnosis.subject_id == patient_id)
        .order_by(Diagnosis.seq_num)
    )
    diagnoses = diagnoses_result.scalars().all()

    meds_result = await db.execute(
        select(Medication)
        .where(Medication.subject_id == patient_id)
        .order_by(Medication.startdate.desc())
    )
    medications = meds_result.scalars().all()

    def admission_duration(a: Admission) -> float | None:
        if a.admittime and a.dischtime:
            return (a.dischtime - a.admittime).total_seconds() / 86400
        return None

    return PatientDetail(
        subject_id=patient.subject_id,
        gender=patient.gender,
        age=_compute_age(patient.dob, patient.dod),
        alive=patient.expire_flag != 1,
        admissions=[
            AdmissionDetail(
                hadm_id=a.hadm_id,
                admittime=a.admittime,
                dischtime=a.dischtime,
                admission_type=a.admission_type,
                diagnosis=a.diagnosis,
                duration_days=admission_duration(a),
            )
            for a in admissions
        ],
        diagnoses=[
            {
                "icd9_code": d.icd9_code,
                "short_title": d.short_title,
                "long_title": d.long_title,
                "seq_num": d.seq_num,
                "hadm_id": d.hadm_id,
            }
            for d in diagnoses
        ],
        medications=[
            {
                "drug": m.drug,
                "dose": f"{m.dose_val_rx} {m.dose_unit_rx}".strip(),
                "route": m.route,
                "startdate": m.startdate,
                "enddate": m.enddate,
            }
            for m in medications
        ],
    )


@router.get("/patients/{patient_id}/labs")
async def get_patient_labs(
    patient_id: int,
    label: str | None = None,
    limit: int = 200,
    db: AsyncSession = Depends(get_db),
):
    stmt = (
        select(LabResult)
        .where(LabResult.subject_id == patient_id)
        .order_by(LabResult.charttime.asc())
        .limit(limit)
    )
    if label:
        stmt = stmt.where(LabResult.label.ilike(f"%{label}%"))
    result = await db.execute(stmt)
    rows = result.scalars().all()
    return [
        {
            "label": r.label,
            "valuenum": r.valuenum,
            "valueuom": r.valueuom,
            "charttime": r.charttime,
            "flag": r.flag,
            "hadm_id": r.hadm_id,
        }
        for r in rows
        if r.valuenum is not None
    ]


@router.get("/patients/{patient_id}/vitals")
async def get_patient_vitals(
    patient_id: int,
    label: str | None = None,
    limit: int = 300,
    db: AsyncSession = Depends(get_db),
):
    stmt = (
        select(Vital)
        .where(Vital.subject_id == patient_id)
        .order_by(Vital.charttime.asc())
        .limit(limit)
    )
    if label:
        stmt = stmt.where(Vital.label.ilike(f"%{label}%"))
    result = await db.execute(stmt)
    rows = result.scalars().all()
    return [
        {
            "label": r.label,
            "valuenum": r.valuenum,
            "valueuom": r.valueuom,
            "charttime": r.charttime,
            "hadm_id": r.hadm_id,
        }
        for r in rows
        if r.valuenum is not None
    ]
