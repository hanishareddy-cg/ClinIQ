"""
Index clinical notes from JSONL staging files into Elasticsearch.

Reads:
  data/processed/notes_staging.jsonl        (from script 01 — MIMIC notes)
  data/processed/synthetic_notes_staging.jsonl  (from script 02 — synthetic notes)

Chunks each note, bulk-indexes into ES, then writes es_doc_id back to PostgreSQL.

Usage:
    python scripts/03_index_notes_elasticsearch.py
"""

import json
import logging
import sys
from pathlib import Path

from elasticsearch import Elasticsearch
from elasticsearch.helpers import BulkIndexError, bulk
from sqlalchemy import create_engine, text

sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.config import get_settings
from backend.es.index_setup import NOTES_INDEX_MAPPING
from backend.utils.text_utils import chunk_note, clean_note_text

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)

PROCESSED = Path("data/processed")
STAGING_FILES = [
    PROCESSED / "notes_staging.jsonl",
    PROCESSED / "synthetic_notes_staging.jsonl",
]


def _ensure_index(es: Elasticsearch, index: str) -> None:
    if not es.indices.exists(index=index):
        es.indices.create(index=index, body=NOTES_INDEX_MAPPING)
        log.info("Created ES index: %s", index)
    else:
        log.info("ES index already exists: %s", index)


def _iter_actions(staging_files: list[Path], index: str):
    """Yield ES bulk action dicts for every chunk of every note."""
    for staging_path in staging_files:
        if not staging_path.exists():
            log.warning("Staging file not found, skipping: %s", staging_path)
            continue

        log.info("Processing %s...", staging_path)
        with staging_path.open() as f:
            for line in f:
                note = json.loads(line)
                text_clean = clean_note_text(note.get("text", ""))
                if not text_clean:
                    continue

                chunks = chunk_note(text_clean)
                for idx, chunk_text in enumerate(chunks):
                    doc_id = f"{note['row_id']}_{idx}"
                    yield {
                        "_index": index,
                        "_id": doc_id,
                        "_source": {
                            "doc_id":       doc_id,
                            "subject_id":   note["subject_id"],
                            "hadm_id":      note.get("hadm_id"),
                            "chartdate":    note.get("chartdate"),
                            "category":     note.get("category", ""),
                            "description":  note.get("description", ""),
                            "text":         chunk_text,
                            "chunk_index":  idx,
                            "chunk_total":  len(chunks),
                            "source_row_id": note["row_id"],
                        },
                    }


def _write_doc_ids_to_postgres(engine, index_name: str, es: Elasticsearch) -> None:
    """
    After indexing, write es_doc_id (the first chunk's doc_id) back to
    clinical_notes_meta so the query pipeline can cross-reference ES hits to PG.
    """
    log.info("Writing es_doc_id back to PostgreSQL...")

    # Scroll through all docs in the index to collect row_id → doc_id mapping
    # Only need chunk_index=0 (first chunk) to represent the note
    result = es.search(
        index=index_name,
        body={
            "query": {"term": {"chunk_index": 0}},
            "_source": ["source_row_id", "doc_id"],
            "size": 10000,
        },
        scroll="2m",
    )

    scroll_id = result.get("_scroll_id")
    hits = result["hits"]["hits"]
    updated = 0

    with engine.begin() as conn:
        while hits:
            for hit in hits:
                row_id = hit["_source"]["source_row_id"]
                doc_id = hit["_source"]["doc_id"]
                conn.execute(
                    text("UPDATE clinical_notes_meta SET es_doc_id = :doc_id WHERE row_id = :row_id"),
                    {"doc_id": doc_id, "row_id": row_id},
                )
                updated += 1

            result = es.scroll(scroll_id=scroll_id, scroll="2m")
            hits = result["hits"]["hits"]

    es.clear_scroll(scroll_id=scroll_id)
    log.info("  → Updated es_doc_id for %d notes in PostgreSQL", updated)


def main():
    settings = get_settings()
    es = Elasticsearch(
        hosts=[{"host": settings.es_host, "port": settings.es_port, "scheme": "http"}],
        request_timeout=60,
    )

    if not es.ping():
        log.error("Elasticsearch not reachable at %s:%d", settings.es_host, settings.es_port)
        log.error("Start with: docker-compose up elasticsearch")
        sys.exit(1)

    index = settings.es_index
    _ensure_index(es, index)

    log.info("Bulk indexing notes...")
    actions = list(_iter_actions(STAGING_FILES, index))

    if not actions:
        log.warning("No actions to index. Run scripts 01 and 02 first.")
        return

    try:
        success, failed = bulk(
            es,
            actions,
            chunk_size=500,
            raise_on_error=True,
        )
        log.info("Indexed %d chunks successfully.", success)
    except BulkIndexError as e:
        log.error("Bulk indexing had %d failures: %s", len(e.errors), e.errors[:3])
        raise

    # Force refresh so docs are immediately searchable for the scroll below
    es.indices.refresh(index=index)

    engine = create_engine(settings.postgres_url_sync, echo=False)
    _write_doc_ids_to_postgres(engine, index, es)

    # Final count
    count = es.count(index=index)["count"]
    log.info("Total documents in index '%s': %d", index, count)


if __name__ == "__main__":
    main()
