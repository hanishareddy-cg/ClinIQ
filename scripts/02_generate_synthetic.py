"""
Generate 50 synthetic patients and load them into PostgreSQL.

Patients have clinically correlated data:
  - Demographics via Faker
  - ICD-9 diagnoses from a curated set
  - Lab values plausible for their diagnoses
  - Discharge summary notes (templated; Claude-enhanced if ANTHROPIC_API_KEY is set)

Usage:
    python scripts/02_generate_synthetic.py
"""

import json
import logging
import random
import sys
from datetime import date, datetime, timedelta
from pathlib import Path

import pandas as pd
from faker import Faker
from sqlalchemy import create_engine, text

sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.config import get_settings
from backend.utils.icd_lookup import ICD9_COMMON

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)

PROCESSED = Path("data/processed")
fake = Faker()
random.seed(42)

# Starting IDs above MIMIC demo range to avoid collisions
SUBJECT_ID_START = 100_000
HADM_ID_START = 200_000
NOTE_ROW_ID_START = 500_000

# ICD-9 conditions with correlated lab abnormalities
# Format: {icd9_code: {lab_label: (low, high, unit, flag_if_outside_normal)}}
CONDITION_LAB_PROFILES: dict[str, dict] = {
    "584.9": {  # AKI
        "Creatinine":    (1.8, 6.5,  "mg/dL",  "abnormal"),
        "Urea Nitrogen": (30,  120,  "mg/dL",  "abnormal"),
        "Potassium":     (4.5, 6.5,  "mEq/L",  "abnormal"),
        "Sodium":        (130, 148,  "mEq/L",  None),
    },
    "428.0": {  # CHF
        "Sodium":        (128, 140,  "mEq/L",  "abnormal"),
        "Hemoglobin":    (8.0, 12.5, "g/dL",   "abnormal"),
        "Creatinine":    (1.2, 3.0,  "mg/dL",  "abnormal"),
        "Troponin T":    (0.01, 2.0, "ng/mL",  "abnormal"),
    },
    "250.00": {  # Diabetes
        "Glucose":       (180, 450,  "mg/dL",  "abnormal"),
        "Hemoglobin":    (9.0, 13.5, "g/dL",   None),
        "Creatinine":    (0.8, 2.5,  "mg/dL",  None),
        "Potassium":     (3.5, 5.5,  "mEq/L",  None),
    },
    "038.9": {  # Sepsis
        "White Blood Cells": (12.0, 30.0, "K/uL",  "abnormal"),
        "Lactate":           (2.5, 10.0,  "mmol/L","abnormal"),
        "Creatinine":        (1.5, 4.0,   "mg/dL", "abnormal"),
        "Platelet Count":    (50,  180,   "K/uL",  "abnormal"),
    },
    "486": {  # Pneumonia
        "White Blood Cells": (11.0, 25.0, "K/uL",  "abnormal"),
        "Hemoglobin":        (9.5,  13.0, "g/dL",  None),
        "Sodium":            (130,  145,  "mEq/L", None),
    },
    "401.9": {  # Hypertension
        "Creatinine":    (0.9, 1.8,  "mg/dL", None),
        "Potassium":     (3.4, 5.2,  "mEq/L", None),
        "Sodium":        (136, 146,  "mEq/L", None),
    },
}

# Normal lab ranges for patients without specific conditions
NORMAL_LAB_RANGES: dict[str, tuple] = {
    "Creatinine":    (0.6, 1.2,  "mg/dL",  None),
    "Potassium":     (3.5, 5.0,  "mEq/L",  None),
    "Sodium":        (136, 145,  "mEq/L",  None),
    "Hemoglobin":    (12.0, 17.5,"g/dL",   None),
    "White Blood Cells": (4.5, 11.0, "K/uL", None),
    "Glucose":       (70,  110,  "mg/dL",  None),
    "Platelet Count":(150, 400,  "K/uL",   None),
}

DISCHARGE_TEMPLATE = """\
DISCHARGE SUMMARY

Patient: {age}-year-old {gender}
Admission Date: {admittime}
Discharge Date: {dischtime}
Admission Type: {admission_type}

PRIMARY DIAGNOSIS:
{primary_dx}

SECONDARY DIAGNOSES:
{secondary_dx}

HOSPITAL COURSE:
Patient presented with {complaint}. {clinical_course}

LABORATORY FINDINGS:
{lab_summary}

MEDICATIONS AT DISCHARGE:
{med_summary}

DISPOSITION:
{disposition}

Attending Physician: {physician}
"""

COMPLAINTS: dict[str, str] = {
    "584.9": "elevated creatinine and decreased urine output",
    "428.0": "shortness of breath and lower extremity edema",
    "250.00": "hyperglycemia and altered mental status",
    "038.9": "fever, hypotension, and altered mental status",
    "486": "productive cough, fever, and hypoxia",
    "401.9": "hypertensive urgency with headache",
    "default": "acute onset of symptoms requiring hospitalization",
}

CLINICAL_COURSES: dict[str, str] = {
    "584.9": "Renal function was monitored closely. IV fluids were administered. Nephrology was consulted. Creatinine trended down with supportive management.",
    "428.0": "Patient was diuresed with IV furosemide with improvement in symptoms. Echocardiogram revealed reduced ejection fraction. Cardiology was consulted.",
    "250.00": "Insulin drip initiated with blood glucose monitoring every hour. Endocrinology was consulted for diabetes management optimization.",
    "038.9": "Blood cultures obtained. Broad-spectrum antibiotics initiated. IV fluids administered. Patient was monitored in the ICU. Cultures finalized and antibiotics narrowed.",
    "486": "Chest X-ray confirmed pneumonia. Antibiotics initiated per culture sensitivities. Respiratory therapy provided. O2 saturation improved.",
    "401.9": "Blood pressure managed with IV labetalol initially, transitioned to oral antihypertensives. Patient remained neurologically intact.",
    "default": "Patient was evaluated and treated. Clinical status improved with appropriate management.",
}


def _random_date(start: date, end: date) -> date:
    delta = (end - start).days
    return start + timedelta(days=random.randint(0, delta))


def _generate_patients(n: int) -> list[dict]:
    patients = []
    for i in range(n):
        age = random.randint(25, 90)
        dob = date.today() - timedelta(days=age * 365 + random.randint(0, 364))
        expire = random.random() < 0.15  # 15% mortality rate
        dod = dob + timedelta(days=age * 365 + random.randint(30, 730)) if expire else None

        patients.append({
            "subject_id": SUBJECT_ID_START + i,
            "gender": random.choice(["M", "F"]),
            "dob": dob,
            "dod": dod,
            "dod_hosp": dod if expire and random.random() < 0.5 else None,
            "expire_flag": 1 if expire else 0,
        })
    return patients


def _generate_admissions(patients: list[dict]) -> list[dict]:
    admissions = []
    hadm_counter = HADM_ID_START
    for p in patients:
        n_admissions = random.randint(1, 3)
        base_date = date.today() - timedelta(days=random.randint(90, 1800))
        for j in range(n_admissions):
            admit = base_date + timedelta(days=j * random.randint(30, 200))
            los = random.randint(2, 14)
            disch = admit + timedelta(days=los)
            admissions.append({
                "hadm_id": hadm_counter,
                "subject_id": p["subject_id"],
                "admittime": datetime.combine(admit, datetime.min.time().replace(hour=random.randint(0, 23))),
                "dischtime": datetime.combine(disch, datetime.min.time().replace(hour=random.randint(0, 23))),
                "admission_type": random.choice(["EMERGENCY", "ELECTIVE", "URGENT"]),
                "diagnosis": None,  # filled after diagnoses are assigned
                "hospital_expire_flag": 0,
            })
            hadm_counter += 1
    return admissions


def _assign_diagnoses(admissions: list[dict]) -> list[dict]:
    condition_pool = list(CONDITION_LAB_PROFILES.keys()) + ["401.9", "272.4", "285.9"]
    diagnoses = []
    diag_id = 1
    for adm in admissions:
        n_dx = random.randint(1, 4)
        selected = random.sample(condition_pool, min(n_dx, len(condition_pool)))
        for seq, code in enumerate(selected, start=1):
            info = ICD9_COMMON.get(code, (code, code))
            short_title, long_title = info
            diagnoses.append({
                "id": diag_id,
                "subject_id": adm["subject_id"],
                "hadm_id": adm["hadm_id"],
                "icd9_code": code,
                "short_title": short_title,
                "long_title": long_title,
                "seq_num": seq,
            })
            if seq == 1:
                adm["diagnosis"] = short_title
            diag_id += 1
    return diagnoses


def _generate_labs(admissions: list[dict], diagnoses: list[dict]) -> list[dict]:
    hadm_to_conditions: dict[int, list[str]] = {}
    for d in diagnoses:
        hadm_to_conditions.setdefault(d["hadm_id"], []).append(d["icd9_code"])

    labs = []
    lab_id = 1
    item_counter = 60000  # synthetic itemids

    for adm in admissions:
        conditions = hadm_to_conditions.get(adm["hadm_id"], [])
        admit_dt: datetime = adm["admittime"]
        disch_dt: datetime = adm["dischtime"]
        los_hours = max(1, int((disch_dt - admit_dt).total_seconds() / 3600))

        # Determine which labs to generate based on conditions
        lab_targets: dict[str, tuple] = {}
        for code in conditions:
            if code in CONDITION_LAB_PROFILES:
                for label, spec in CONDITION_LAB_PROFILES[code].items():
                    if label not in lab_targets:
                        lab_targets[label] = spec

        # Fill in normal ranges for missing common labs
        for label, spec in NORMAL_LAB_RANGES.items():
            if label not in lab_targets:
                lab_targets[label] = spec

        # Generate 2-4 draws per lab over the admission
        for label, (low, high, unit, flag) in lab_targets.items():
            n_draws = random.randint(2, 4)
            for draw in range(n_draws):
                offset_hours = int(draw * los_hours / n_draws) + random.randint(0, 4)
                chart_dt = admit_dt + timedelta(hours=offset_hours)
                val = round(random.uniform(low, high), 2)
                labs.append({
                    "id": lab_id,
                    "subject_id": adm["subject_id"],
                    "hadm_id": adm["hadm_id"],
                    "itemid": item_counter,
                    "label": label,
                    "charttime": chart_dt,
                    "value": str(val),
                    "valuenum": val,
                    "valueuom": unit,
                    "flag": flag,
                })
                lab_id += 1
            item_counter += 1

    return labs


def _generate_medications(admissions: list[dict]) -> list[dict]:
    med_pool = [
        ("Metoprolol Succinate", "25 mg",    "PO"),
        ("Lisinopril",           "10 mg",    "PO"),
        ("Furosemide",           "40 mg",    "PO"),
        ("Aspirin",              "81 mg",    "PO"),
        ("Atorvastatin",         "40 mg",    "PO"),
        ("Insulin Regular",      "per scale","IV"),
        ("Heparin",              "5000 unit","SC"),
        ("Pantoprazole",         "40 mg",    "PO"),
        ("Metformin",            "500 mg",   "PO"),
        ("Amlodipine",           "5 mg",     "PO"),
        ("Vancomycin",           "1 g",      "IV"),
        ("Piperacillin-Tazobactam","3.375 g","IV"),
    ]
    meds = []
    med_id = 1
    for adm in admissions:
        n_meds = random.randint(2, 6)
        selected = random.sample(med_pool, min(n_meds, len(med_pool)))
        for drug, dose, route in selected:
            meds.append({
                "id": med_id,
                "subject_id": adm["subject_id"],
                "hadm_id": adm["hadm_id"],
                "drug": drug,
                "drug_type": "MAIN",
                "formulary_drug_cd": drug[:8].upper().replace(" ", ""),
                "dose_val_rx": dose.split()[0],
                "dose_unit_rx": dose.split()[1] if len(dose.split()) > 1 else "",
                "route": route,
                "startdate": adm["admittime"],
                "enddate": adm["dischtime"],
            })
            med_id += 1
    return meds


def _generate_notes(
    patients: list[dict],
    admissions: list[dict],
    diagnoses: list[dict],
    labs: list[dict],
    meds: list[dict],
) -> list[dict]:
    """Generate one discharge summary per admission using a template."""
    hadm_to_dx: dict[int, list[dict]] = {}
    for d in diagnoses:
        hadm_to_dx.setdefault(d["hadm_id"], []).append(d)

    hadm_to_labs: dict[int, list[dict]] = {}
    for lab in labs:
        hadm_to_labs.setdefault(lab["hadm_id"], []).append(lab)

    hadm_to_meds: dict[int, list[dict]] = {}
    for med in meds:
        hadm_to_meds.setdefault(med["hadm_id"], []).append(med)

    subject_to_patient: dict[int, dict] = {p["subject_id"]: p for p in patients}

    notes = []
    row_id = NOTE_ROW_ID_START

    for adm in admissions:
        pt = subject_to_patient[adm["subject_id"]]
        dxs = sorted(hadm_to_dx.get(adm["hadm_id"], []), key=lambda x: x["seq_num"])
        adm_labs = hadm_to_labs.get(adm["hadm_id"], [])
        adm_meds = hadm_to_meds.get(adm["hadm_id"], [])

        if not dxs:
            continue

        primary_code = dxs[0]["icd9_code"]
        age = (adm["admittime"].date() - pt["dob"]).days // 365

        lab_lines = []
        seen_labels: set[str] = set()
        for lab in sorted(adm_labs, key=lambda x: x["charttime"], reverse=True):
            if lab["label"] not in seen_labels:
                flag_str = f" [{lab['flag'].upper()}]" if lab["flag"] else ""
                lab_lines.append(f"  {lab['label']}: {lab['value']} {lab['valueuom']}{flag_str}")
                seen_labels.add(lab["label"])

        med_lines = [f"  {m['drug']} {m['dose_val_rx']} {m['dose_unit_rx']} {m['route']}"
                     for m in adm_meds]

        text = DISCHARGE_TEMPLATE.format(
            age=age,
            gender="male" if pt["gender"] == "M" else "female",
            admittime=adm["admittime"].strftime("%Y-%m-%d"),
            dischtime=adm["dischtime"].strftime("%Y-%m-%d"),
            admission_type=adm["admission_type"],
            primary_dx=f"{dxs[0]['long_title']} ({dxs[0]['icd9_code']})",
            secondary_dx="\n".join(
                f"  {d['long_title']} ({d['icd9_code']})" for d in dxs[1:]
            ) or "  None",
            complaint=COMPLAINTS.get(primary_code, COMPLAINTS["default"]),
            clinical_course=CLINICAL_COURSES.get(primary_code, CLINICAL_COURSES["default"]),
            lab_summary="\n".join(lab_lines) or "  No labs available",
            med_summary="\n".join(med_lines) or "  None",
            disposition=random.choice([
                "Discharged to home with follow-up in 1 week.",
                "Discharged to skilled nursing facility.",
                "Discharged to home with home health services.",
                "Transferred to rehabilitation facility.",
            ]),
            physician=fake.name(),
        )

        notes.append({
            "row_id": row_id,
            "subject_id": adm["subject_id"],
            "hadm_id": adm["hadm_id"],
            "chartdate": adm["dischtime"].date(),
            "category": "Discharge summary",
            "description": "Report",
            "text": text,
        })
        row_id += 1

    return notes


def _write_to_db(engine, patients, admissions, diagnoses, meds, labs, notes_meta):
    with engine.begin() as conn:
        for table in ["clinical_notes_meta", "lab_results", "vitals",
                      "medications", "diagnoses", "admissions", "patients"]:
            # Only delete synthetic rows (subject_id >= SUBJECT_ID_START)
            if table == "patients":
                conn.execute(text(f"DELETE FROM {table} WHERE subject_id >= {SUBJECT_ID_START}"))
            elif table == "admissions":
                conn.execute(text(f"DELETE FROM {table} WHERE subject_id >= {SUBJECT_ID_START}"))
            else:
                conn.execute(text(f"DELETE FROM {table} WHERE subject_id >= {SUBJECT_ID_START}"))

    # These tables use DB-managed auto-increment PKs — drop the locally generated id
    AUTO_PK_TABLES = {"diagnoses", "medications", "lab_results", "vitals", "clinical_notes_meta"}

    def _insert(data: list[dict], table: str) -> None:
        if not data:
            return
        df = pd.DataFrame(data)
        if table in AUTO_PK_TABLES and "id" in df.columns:
            df = df.drop(columns=["id"])
        df.to_sql(table, engine, if_exists="append", index=False,
                  method="multi", chunksize=500)
        log.info("  → %s: %d rows", table, len(df))

    _insert(patients, "patients")
    _insert(admissions, "admissions")
    _insert(diagnoses, "diagnoses")
    _insert(meds, "medications")
    _insert(labs, "lab_results")
    _insert([{k: v for k, v in n.items() if k != "text"} | {"es_doc_id": None}
             for n in notes_meta], "clinical_notes_meta")


def main():
    settings = get_settings()
    engine = create_engine(settings.postgres_url_sync, echo=False)

    n = 50
    log.info("Generating %d synthetic patients...", n)

    patients = _generate_patients(n)
    admissions = _generate_admissions(patients)
    diagnoses = _assign_diagnoses(admissions)
    labs = _generate_labs(admissions, diagnoses)
    meds = _generate_medications(admissions)
    notes = _generate_notes(patients, admissions, diagnoses, labs, meds)

    log.info("Writing to PostgreSQL...")
    _write_to_db(engine, patients, admissions, diagnoses, meds, labs, notes)

    # Stage notes to JSONL for Elasticsearch
    PROCESSED.mkdir(exist_ok=True)
    staging_path = PROCESSED / "synthetic_notes_staging.jsonl"
    with staging_path.open("w") as f:
        for note in notes:
            f.write(json.dumps({
                "row_id": note["row_id"],
                "subject_id": note["subject_id"],
                "hadm_id": note["hadm_id"],
                "chartdate": str(note["chartdate"]),
                "category": note["category"],
                "description": note["description"],
                "text": note["text"],
            }) + "\n")

    log.info("Staged %d synthetic notes to %s", len(notes), staging_path)
    log.info("Done. Totals: %d patients, %d admissions, %d diagnoses, %d labs, %d meds, %d notes",
             len(patients), len(admissions), len(diagnoses), len(labs), len(meds), len(notes))


if __name__ == "__main__":
    main()
