"""
Smoke test: verifies the data layer is loaded and queryable.

Checks:
  1. PostgreSQL — row counts for each table
  2. Elasticsearch — document count and a sample search
  3. Cross-reference — a known patient's labs and note es_doc_id

Usage:
    python scripts/04_smoke_test_pipeline.py
"""

import sys
from pathlib import Path

from elasticsearch import Elasticsearch
from sqlalchemy import create_engine, text

sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.config import get_settings

PASS = "\033[92m PASS\033[0m"
FAIL = "\033[91m FAIL\033[0m"


def check(label: str, condition: bool, detail: str = "") -> bool:
    status = PASS if condition else FAIL
    print(f"  [{status}] {label}" + (f" — {detail}" if detail else ""))
    return condition


def main():
    settings = get_settings()
    engine = create_engine(settings.postgres_url_sync, echo=False)
    es = Elasticsearch(
        hosts=[{"host": settings.es_host, "port": settings.es_port, "scheme": "http"}],
    )

    failures = 0
    print("\n=== PostgreSQL Checks ===")

    with engine.connect() as conn:
        counts = {
            "patients":    conn.execute(text("SELECT COUNT(*) FROM patients")).scalar(),
            "admissions":  conn.execute(text("SELECT COUNT(*) FROM admissions")).scalar(),
            "diagnoses":   conn.execute(text("SELECT COUNT(*) FROM diagnoses")).scalar(),
            "medications": conn.execute(text("SELECT COUNT(*) FROM medications")).scalar(),
            "lab_results": conn.execute(text("SELECT COUNT(*) FROM lab_results")).scalar(),
            "clinical_notes_meta": conn.execute(text("SELECT COUNT(*) FROM clinical_notes_meta")).scalar(),
        }

    for table, count in counts.items():
        ok = check(f"{table} has rows", count > 0, f"{count} rows")
        if not ok:
            failures += 1

    # Check at least one note has es_doc_id populated
    with engine.connect() as conn:
        linked = conn.execute(
            text("SELECT COUNT(*) FROM clinical_notes_meta WHERE es_doc_id IS NOT NULL")
        ).scalar()
    ok = check("notes linked to ES", linked > 0, f"{linked} notes have es_doc_id")
    if not ok:
        failures += 1

    print("\n=== Elasticsearch Checks ===")

    ok = check("ES is reachable", es.ping())
    if not ok:
        failures += 1
        print("  Cannot reach Elasticsearch — skipping ES checks")
    else:
        doc_count = es.count(index=settings.es_index).get("count", 0)
        ok = check("ES index has documents", doc_count > 0, f"{doc_count} chunks")
        if not ok:
            failures += 1

        # Sample search — should find something for "creatinine"
        result = es.search(
            index=settings.es_index,
            body={
                "query": {"match": {"text": "creatinine"}},
                "size": 1,
            },
        )
        hits = result["hits"]["total"]["value"]
        ok = check("BM25 search returns results", hits > 0, f"{hits} hits for 'creatinine'")
        if not ok:
            failures += 1

    print("\n=== Cross-Reference Check ===")

    # Pick the first patient with labs and check the pipeline can find them
    with engine.connect() as conn:
        row = conn.execute(
            text("SELECT DISTINCT subject_id FROM lab_results LIMIT 1")
        ).fetchone()
        if row:
            subject_id = row[0]
            lab_count = conn.execute(
                text("SELECT COUNT(*) FROM lab_results WHERE subject_id = :sid"),
                {"sid": subject_id},
            ).scalar()
            ok = check(f"Patient {subject_id} has labs", lab_count > 0, f"{lab_count} labs")
            if not ok:
                failures += 1
        else:
            print(f"  [{FAIL}] No patients with lab results found")
            failures += 1

    print(f"\n{'All checks passed.' if failures == 0 else f'{failures} check(s) failed.'}")
    sys.exit(0 if failures == 0 else 1)


if __name__ == "__main__":
    main()
