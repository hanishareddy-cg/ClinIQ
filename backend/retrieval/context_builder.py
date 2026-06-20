from datetime import datetime

from backend.models.db_models import Admission, Patient
from backend.models.schemas import Citation
from backend.retrieval.types import RetrievedFact, RetrievedNote


def build_context(
    facts: list[RetrievedFact],
    notes: list[RetrievedNote],
    patient: Patient,
    admissions: list[Admission],
) -> tuple[str, list[Citation]]:
    """
    Assemble retrieved evidence into a structured context string for the LLM.
    Returns (context_string, citations).

    Every labeled bracket ([LAB-1], [MED-2], etc.) maps to one Citation object
    that the API returns alongside the answer — this is what powers the source panel.
    """
    citations: list[Citation] = []
    lines: list[str] = []

    # --- Patient demographics ---
    age = _compute_age(patient.dob, patient.dod)
    status = "Deceased" if patient.expire_flag == 1 else "Alive"
    lines.append("=== PATIENT DEMOGRAPHICS ===")
    lines.append(
        f"Patient ID: {patient.subject_id} | Gender: {patient.gender or 'Unknown'} "
        f"| Age: {age or 'Unknown'} | Status: {status}"
    )
    lines.append("")

    # --- Admissions (most recent 3) ---
    if admissions:
        lines.append("=== RECENT ADMISSIONS ===")
        for i, adm in enumerate(admissions[:3], 1):
            admit = _fmt_dt(adm.admittime)
            disch = _fmt_dt(adm.dischtime)
            lines.append(
                f"[ADM-{i}] Admission {adm.hadm_id} | {admit} → {disch} "
                f"| {adm.admission_type or ''} | {adm.diagnosis or ''}"
            )
        lines.append("")

    # --- Separate facts by type ---
    labs     = [f for f in facts if f.source_type == "lab"]
    meds     = [f for f in facts if f.source_type == "medication"]
    vitals   = [f for f in facts if f.source_type == "vital"]
    diagnoses = [f for f in facts if f.source_type == "diagnosis"]

    if labs:
        lines.append("=== LABORATORY RESULTS ===")
        for i, lab in enumerate(labs, 1):
            cid = f"LAB-{i}"
            flag_str = f" [{lab.flag.upper()}]" if lab.flag else ""
            unit_str = f" {lab.unit}" if lab.unit else ""
            ts = _fmt_dt(lab.timestamp)
            lines.append(
                f"[{cid}] {lab.label}: {lab.value}{unit_str}{flag_str} | "
                f"Admission {lab.hadm_id} | {ts}"
            )
            citations.append(Citation(
                id=cid,
                source_type="lab",
                label=lab.label,
                value=lab.value,
                unit=lab.unit,
                flag=lab.flag,
                timestamp=lab.timestamp,
                hadm_id=lab.hadm_id,
            ))
        lines.append("")

    if meds:
        lines.append("=== MEDICATIONS ===")
        for i, med in enumerate(meds, 1):
            cid = f"MED-{i}"
            route = f" | Route: {med.unit}" if med.unit else ""
            start = _fmt_dt(med.timestamp)
            end_dt = med.metadata.get("enddate")
            end = _fmt_dt(end_dt) if end_dt else "ongoing"
            lines.append(
                f"[{cid}] {med.label} {med.value}{route} | "
                f"Started: {start} | Ended: {end}"
            )
            citations.append(Citation(
                id=cid,
                source_type="medication",
                label=med.label,
                value=med.value,
                unit=med.unit,
                timestamp=med.timestamp,
                hadm_id=med.hadm_id,
            ))
        lines.append("")

    if vitals:
        lines.append("=== VITAL SIGNS ===")
        for i, vital in enumerate(vitals, 1):
            cid = f"VIT-{i}"
            unit_str = f" {vital.unit}" if vital.unit else ""
            ts = _fmt_dt(vital.timestamp)
            lines.append(f"[{cid}] {vital.label}: {vital.value}{unit_str} | {ts}")
            citations.append(Citation(
                id=cid,
                source_type="vital",
                label=vital.label,
                value=vital.value,
                unit=vital.unit,
                timestamp=vital.timestamp,
                hadm_id=vital.hadm_id,
            ))
        lines.append("")

    if diagnoses:
        lines.append("=== DIAGNOSES ===")
        for i, dx in enumerate(diagnoses, 1):
            cid = f"DX-{i}"
            primary = " [Primary]" if dx.seq_num == 1 else ""
            icd = dx.metadata.get("icd9_code", "")
            icd_str = f" ({icd})" if icd else ""
            lines.append(f"[{cid}] {dx.value or dx.label}{icd_str}{primary}")
            citations.append(Citation(
                id=cid,
                source_type="diagnosis",
                label=dx.label,
                value=dx.value,
                hadm_id=dx.hadm_id,
            ))
        lines.append("")

    if notes:
        lines.append("=== CLINICAL NOTES ===")
        for i, note in enumerate(notes, 1):
            cid = f"NOTE-{i}"
            lines.append(
                f"[{cid}] {note.category} | {note.chartdate or 'Unknown date'} "
                f"| Admission {note.hadm_id}"
            )
            for snippet in note.highlights[:2]:
                lines.append(f"  ...{snippet}...")
            citations.append(Citation(
                id=cid,
                source_type="note",
                label=note.category,
                category=note.category,
                excerpt=note.highlights[0] if note.highlights else None,
                hadm_id=note.hadm_id,
            ))
        lines.append("")

    return "\n".join(lines), citations


def _fmt_dt(dt) -> str:
    if dt is None:
        return "Unknown"
    if isinstance(dt, datetime):
        return dt.strftime("%Y-%m-%d %H:%M")
    return str(dt)


def _compute_age(dob, dod) -> int | None:
    if dob is None:
        return None
    from datetime import date
    end = dod or date.today()
    age = end.year - dob.year - ((end.month, end.day) < (dob.month, dob.day))
    return min(age, 89)
