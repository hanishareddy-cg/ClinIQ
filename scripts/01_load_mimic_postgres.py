"""
ETL: MIMIC-III demo CSVs → PostgreSQL

Usage:
    python scripts/01_load_mimic_postgres.py

Expects MIMIC-III demo CSVs in data/raw/.
Download from: https://physionet.org/content/mimiciii-demo/1.4/
"""

import json
import logging
import sys
from pathlib import Path

import pandas as pd
from sqlalchemy import create_engine, text

# Add project root to path so backend imports work
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.config import get_settings

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)

RAW = Path("data/raw")
PROCESSED = Path("data/processed")

# Curated lab itemids → label. Covers CBC, BMP, LFTs, coagulation, ABG.
LAB_ITEMIDS: dict[int, str] = {
    50802: "Base Excess",
    50813: "Lactate",
    50818: "pCO2",
    50820: "pH",
    50821: "pO2",
    50861: "ALT",
    50863: "Alkaline Phosphatase",
    50867: "Amylase",
    50878: "AST",
    50885: "Bilirubin Total",
    50893: "Calcium Total",
    50902: "Chloride",
    50912: "Creatinine",
    50931: "Glucose",
    50956: "Lipase",
    50960: "Magnesium",
    50970: "Phosphate",
    50971: "Potassium",
    50976: "Total Protein",
    50983: "Sodium",
    51003: "Troponin T",
    51006: "Urea Nitrogen",
    51144: "Bands",
    51200: "Eosinophils",
    51214: "Fibrinogen",
    51221: "Hematocrit",
    51222: "Hemoglobin",
    51237: "INR",
    51248: "MCH",
    51249: "MCHC",
    51250: "MCV",
    51256: "Neutrophils",
    51265: "Platelet Count",
    51277: "RDW",
    51301: "White Blood Cells",
}

# Vital itemids — CareVue and MetaVision both present in MIMIC demo
VITAL_ITEMIDS: dict[int, str] = {
    # MetaVision
    220045: "Heart Rate",
    220179: "Non Invasive Blood Pressure systolic",
    220180: "Non Invasive Blood Pressure diastolic",
    220210: "Respiratory Rate",
    220277: "O2 Saturation",
    223761: "Temperature F",
    223762: "Temperature C",
    # CareVue
    211:   "Heart Rate",
    455:   "Non Invasive Blood Pressure systolic",
    8441:  "Non Invasive Blood Pressure diastolic",
    618:   "Respiratory Rate",
    646:   "O2 Saturation",
    676:   "Temperature C",
    678:   "Temperature F",
}


def _check_raw_files() -> None:
    required = [
        "PATIENTS.csv", "ADMISSIONS.csv", "DIAGNOSES_ICD.csv",
        "D_ICD_DIAGNOSES.csv", "PRESCRIPTIONS.csv", "LABEVENTS.csv",
        "D_LABITEMS.csv", "CHARTEVENTS.csv", "NOTEEVENTS.csv",
    ]
    missing = [f for f in required if not (RAW / f).exists()]
    if missing:
        log.error("Missing MIMIC files in data/raw/: %s", missing)
        log.error("Download from: https://physionet.org/content/mimiciii-demo/1.4/")
        sys.exit(1)


def _load_patients(engine) -> int:
    log.info("Loading PATIENTS...")
    df = pd.read_csv(RAW / "PATIENTS.csv", low_memory=False)
    df.columns = df.columns.str.lower()

    df = df.rename(columns={"subject_id": "subject_id", "dob": "dob",
                             "dod": "dod", "dod_hosp": "dod_hosp",
                             "expire_flag": "expire_flag"})

    df["dob"] = pd.to_datetime(df["dob"], errors="coerce").dt.date
    df["dod"] = pd.to_datetime(df["dod"], errors="coerce").dt.date
    df["dod_hosp"] = pd.to_datetime(df["dod_hosp"], errors="coerce").dt.date

    keep = ["subject_id", "gender", "dob", "dod", "dod_hosp", "expire_flag"]
    df = df[keep]

    with engine.begin() as conn:
        conn.execute(text("TRUNCATE patients CASCADE"))

    df.to_sql("patients", engine, if_exists="append", index=False,
              method="multi", chunksize=500)
    log.info("  → %d patients", len(df))
    return len(df)


def _load_admissions(engine) -> int:
    log.info("Loading ADMISSIONS...")
    df = pd.read_csv(RAW / "ADMISSIONS.csv", low_memory=False)
    df.columns = df.columns.str.lower()

    df["admittime"] = pd.to_datetime(df["admittime"], errors="coerce")
    df["dischtime"] = pd.to_datetime(df["dischtime"], errors="coerce")

    keep = ["hadm_id", "subject_id", "admittime", "dischtime",
            "admission_type", "diagnosis", "hospital_expire_flag"]
    df = df[keep]

    with engine.begin() as conn:
        conn.execute(text("TRUNCATE admissions CASCADE"))

    df.to_sql("admissions", engine, if_exists="append", index=False,
              method="multi", chunksize=500)
    log.info("  → %d admissions", len(df))
    return len(df)


def _load_diagnoses(engine) -> int:
    log.info("Loading DIAGNOSES_ICD...")
    diag = pd.read_csv(RAW / "DIAGNOSES_ICD.csv", low_memory=False)
    diag.columns = diag.columns.str.lower()

    lookup = pd.read_csv(RAW / "D_ICD_DIAGNOSES.csv", low_memory=False)
    lookup.columns = lookup.columns.str.lower()
    lookup = lookup[["icd9_code", "short_title", "long_title"]]

    df = diag.merge(lookup, on="icd9_code", how="left")
    df = df[["subject_id", "hadm_id", "icd9_code", "seq_num",
             "short_title", "long_title"]].dropna(subset=["subject_id", "hadm_id"])
    df["id"] = range(1, len(df) + 1)

    with engine.begin() as conn:
        conn.execute(text("TRUNCATE diagnoses"))

    df.to_sql("diagnoses", engine, if_exists="append", index=False,
              method="multi", chunksize=1000)
    log.info("  → %d diagnosis rows", len(df))
    return len(df)


def _load_medications(engine) -> int:
    log.info("Loading PRESCRIPTIONS...")
    df = pd.read_csv(RAW / "PRESCRIPTIONS.csv", low_memory=False)
    df.columns = df.columns.str.lower()

    df = df.dropna(subset=["drug"])
    df["startdate"] = pd.to_datetime(df["startdate"], errors="coerce")
    df["enddate"] = pd.to_datetime(df["enddate"], errors="coerce")

    keep = ["subject_id", "hadm_id", "drug", "drug_type", "formulary_drug_cd",
            "dose_val_rx", "dose_unit_rx", "route", "startdate", "enddate"]
    df = df[keep]
    df["id"] = range(1, len(df) + 1)

    with engine.begin() as conn:
        conn.execute(text("TRUNCATE medications"))

    df.to_sql("medications", engine, if_exists="append", index=False,
              method="multi", chunksize=1000)
    log.info("  → %d medication rows", len(df))
    return len(df)


def _load_labs(engine) -> int:
    log.info("Loading LABEVENTS (filtered to %d itemids)...", len(LAB_ITEMIDS))
    df = pd.read_csv(RAW / "LABEVENTS.csv", low_memory=False)
    df.columns = df.columns.str.lower()

    df = df[df["itemid"].isin(LAB_ITEMIDS.keys())].copy()
    df["label"] = df["itemid"].map(LAB_ITEMIDS)
    df["charttime"] = pd.to_datetime(df["charttime"], errors="coerce")
    df["valuenum"] = pd.to_numeric(df["valuenum"], errors="coerce")

    # Normalize flag: MIMIC uses "abnormal" and "delta" — lowercase and keep nulls
    df["flag"] = df["flag"].str.lower().where(df["flag"].notna(), other=None)

    keep = ["subject_id", "hadm_id", "itemid", "label", "charttime",
            "value", "valuenum", "valueuom", "flag"]
    df = df[keep]
    df["id"] = range(1, len(df) + 1)

    with engine.begin() as conn:
        conn.execute(text("TRUNCATE lab_results"))

    df.to_sql("lab_results", engine, if_exists="append", index=False,
              method="multi", chunksize=2000)
    log.info("  → %d lab result rows", len(df))
    return len(df)


def _load_vitals(engine) -> int:
    log.info("Loading CHARTEVENTS (vitals only)...")
    # CHARTEVENTS is large even in demo — read in chunks, filter early
    chunks = []
    for chunk in pd.read_csv(RAW / "CHARTEVENTS.csv", low_memory=False,
                              chunksize=50_000):
        chunk.columns = chunk.columns.str.lower()
        filtered = chunk[chunk["itemid"].isin(VITAL_ITEMIDS.keys())].copy()
        if not filtered.empty:
            chunks.append(filtered)

    if not chunks:
        log.warning("  No vital rows found — CHARTEVENTS may be empty in this demo version")
        return 0

    df = pd.concat(chunks, ignore_index=True)
    df["label"] = df["itemid"].map(VITAL_ITEMIDS)
    df["charttime"] = pd.to_datetime(df["charttime"], errors="coerce")
    df["valuenum"] = pd.to_numeric(df["valuenum"], errors="coerce")

    # Drop rows where valuenum is null — vital signs without numeric values aren't useful
    df = df.dropna(subset=["valuenum"])

    keep = ["subject_id", "hadm_id", "itemid", "label", "charttime",
            "valuenum", "valueuom"]
    df = df[keep]
    df["id"] = range(1, len(df) + 1)

    with engine.begin() as conn:
        conn.execute(text("TRUNCATE vitals"))

    df.to_sql("vitals", engine, if_exists="append", index=False,
              method="multi", chunksize=2000)
    log.info("  → %d vital rows", len(df))
    return len(df)


def _load_notes(engine) -> int:
    log.info("Loading NOTEEVENTS...")
    df = pd.read_csv(RAW / "NOTEEVENTS.csv", low_memory=False)
    df.columns = df.columns.str.lower()

    # Drop error notes
    if "iserror" in df.columns:
        df = df[df["iserror"].isna() | (df["iserror"] == 0)]

    df["chartdate"] = pd.to_datetime(df["chartdate"], errors="coerce").dt.date

    # Write metadata to PostgreSQL
    meta = df[["row_id", "subject_id", "hadm_id", "chartdate",
               "category", "description"]].copy()
    meta["es_doc_id"] = None  # filled in by script 03

    with engine.begin() as conn:
        conn.execute(text("TRUNCATE clinical_notes_meta"))

    meta.to_sql("clinical_notes_meta", engine, if_exists="append", index=False,
                method="multi", chunksize=1000)
    log.info("  → %d note metadata rows", len(meta))

    # Stage full text to JSONL for Elasticsearch ingestion
    PROCESSED.mkdir(exist_ok=True)
    staging_path = PROCESSED / "notes_staging.jsonl"
    with staging_path.open("w") as f:
        for _, row in df.iterrows():
            record = {
                "row_id": int(row["row_id"]),
                "subject_id": int(row["subject_id"]),
                "hadm_id": int(row["hadm_id"]) if pd.notna(row.get("hadm_id")) else None,
                "chartdate": str(row["chartdate"]) if pd.notna(row.get("chartdate")) else None,
                "category": str(row["category"]) if pd.notna(row.get("category")) else "",
                "description": str(row["description"]) if pd.notna(row.get("description")) else "",
                "text": str(row["text"]) if pd.notna(row.get("text")) else "",
            }
            f.write(json.dumps(record) + "\n")

    log.info("  → Staged %d notes to %s", len(df), staging_path)
    return len(df)


def main():
    _check_raw_files()

    settings = get_settings()
    engine = create_engine(settings.postgres_url_sync, echo=False)

    # Import models so metadata is populated, then create tables
    import backend.models.db_models  # noqa: F401
    from backend.db.session import Base
    Base.metadata.create_all(engine)
    log.info("Tables created/verified.")

    counts = {
        "patients":    _load_patients(engine),
        "admissions":  _load_admissions(engine),
        "diagnoses":   _load_diagnoses(engine),
        "medications": _load_medications(engine),
        "labs":        _load_labs(engine),
        "vitals":      _load_vitals(engine),
        "notes":       _load_notes(engine),
    }

    log.info("ETL complete. Row counts: %s", counts)


if __name__ == "__main__":
    main()
