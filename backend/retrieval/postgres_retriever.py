from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.db_models import Diagnosis, LabResult, Medication, Vital
from backend.retrieval.types import RetrievedFact


def _lab_row_to_fact(row: LabResult) -> RetrievedFact:
    return RetrievedFact(
        source_type="lab",
        subject_id=row.subject_id,
        hadm_id=row.hadm_id,
        timestamp=row.charttime,
        label=row.label or "",
        value=row.value or (str(row.valuenum) if row.valuenum is not None else ""),
        unit=row.valueuom,
        flag=row.flag,
        seq_num=None,
    )


def _med_row_to_fact(row: Medication) -> RetrievedFact:
    dose = f"{row.dose_val_rx or ''} {row.dose_unit_rx or ''}".strip()
    return RetrievedFact(
        source_type="medication",
        subject_id=row.subject_id,
        hadm_id=row.hadm_id,
        timestamp=row.startdate,
        label=row.drug or "",
        value=dose,
        unit=row.route,
        flag=None,
        seq_num=None,
        metadata={"enddate": row.enddate},
    )


def _vital_row_to_fact(row: Vital) -> RetrievedFact:
    return RetrievedFact(
        source_type="vital",
        subject_id=row.subject_id,
        hadm_id=row.hadm_id,
        timestamp=row.charttime,
        label=row.label or "",
        value=str(row.valuenum) if row.valuenum is not None else "",
        unit=row.valueuom,
        flag=None,
        seq_num=None,
    )


def _diag_row_to_fact(row: Diagnosis) -> RetrievedFact:
    return RetrievedFact(
        source_type="diagnosis",
        subject_id=row.subject_id,
        hadm_id=row.hadm_id,
        timestamp=None,
        label=row.short_title or row.icd9_code or "",
        value=row.long_title or "",
        unit=None,
        flag=None,
        seq_num=row.seq_num,
        metadata={"icd9_code": row.icd9_code},
    )


async def get_labs(
    session: AsyncSession,
    subject_id: int,
    lab_names: list[str],
    hadm_id: int | None = None,
    limit: int = 20,
) -> list[RetrievedFact]:
    stmt = select(LabResult).where(LabResult.subject_id == subject_id)

    if lab_names:
        stmt = stmt.where(
            or_(*[LabResult.label.ilike(f"%{name}%") for name in lab_names])
        )
    if hadm_id:
        stmt = stmt.where(LabResult.hadm_id == hadm_id)

    stmt = stmt.order_by(LabResult.charttime.desc()).limit(limit)
    result = await session.execute(stmt)
    return [_lab_row_to_fact(r) for r in result.scalars().all()]


async def get_medications(
    session: AsyncSession,
    subject_id: int,
    drug_names: list[str],
    hadm_id: int | None = None,
) -> list[RetrievedFact]:
    stmt = select(Medication).where(Medication.subject_id == subject_id)

    if drug_names:
        stmt = stmt.where(
            or_(*[Medication.drug.ilike(f"%{name}%") for name in drug_names])
        )
    if hadm_id:
        stmt = stmt.where(Medication.hadm_id == hadm_id)

    stmt = stmt.order_by(Medication.startdate.desc()).limit(30)
    result = await session.execute(stmt)
    return [_med_row_to_fact(r) for r in result.scalars().all()]


async def get_vitals(
    session: AsyncSession,
    subject_id: int,
    vital_names: list[str],
    hadm_id: int | None = None,
    limit: int = 30,
) -> list[RetrievedFact]:
    stmt = select(Vital).where(Vital.subject_id == subject_id)

    if vital_names:
        stmt = stmt.where(
            or_(*[Vital.label.ilike(f"%{name}%") for name in vital_names])
        )
    if hadm_id:
        stmt = stmt.where(Vital.hadm_id == hadm_id)

    stmt = stmt.order_by(Vital.charttime.desc()).limit(limit)
    result = await session.execute(stmt)
    return [_vital_row_to_fact(r) for r in result.scalars().all()]


async def get_diagnoses(
    session: AsyncSession,
    subject_id: int,
    keyword_filter: list[str],
) -> list[RetrievedFact]:
    stmt = select(Diagnosis).where(Diagnosis.subject_id == subject_id)

    if keyword_filter:
        stmt = stmt.where(
            or_(
                *[Diagnosis.long_title.ilike(f"%{kw}%") for kw in keyword_filter],
                *[Diagnosis.short_title.ilike(f"%{kw}%") for kw in keyword_filter],
                *[Diagnosis.icd9_code.ilike(f"%{kw}%") for kw in keyword_filter],
            )
        )

    stmt = stmt.order_by(Diagnosis.seq_num).limit(20)
    result = await session.execute(stmt)
    return [_diag_row_to_fact(r) for r in result.scalars().all()]
