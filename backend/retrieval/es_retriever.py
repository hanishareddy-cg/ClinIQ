from elasticsearch import AsyncElasticsearch

from backend.config import get_settings
from backend.retrieval.types import RetrievedNote


async def search_notes(
    es: AsyncElasticsearch,
    subject_id: int,
    query_text: str,
    categories: list[str] | None = None,
    hadm_id: int | None = None,
    top_k: int = 5,
) -> list[RetrievedNote]:
    settings = get_settings()

    # subject_id goes in filter (not must) so it doesn't corrupt BM25 scoring
    filters: list[dict] = [{"term": {"subject_id": subject_id}}]
    if categories:
        filters.append({"terms": {"category": categories}})
    if hadm_id:
        filters.append({"term": {"hadm_id": hadm_id}})

    body = {
        "size": top_k,
        "query": {
            "bool": {
                "must": [
                    {
                        "multi_match": {
                            "query": query_text,
                            "fields": ["text^2"],
                            "type": "best_fields",
                            "operator": "or",
                            "minimum_should_match": "30%",
                        }
                    }
                ],
                "filter": filters,
            }
        },
        "highlight": {
            "fields": {
                "text": {
                    "fragment_size": 250,
                    "number_of_fragments": 3,
                    "pre_tags": ["**"],
                    "post_tags": ["**"],
                }
            }
        },
        "_source": [
            "doc_id", "subject_id", "hadm_id", "chartdate",
            "category", "source_row_id", "chunk_index",
        ],
    }

    try:
        result = await es.search(index=settings.es_index, body=body)
    except Exception:
        return []

    hits = result["hits"]["hits"]
    if not hits:
        return []

    max_score = hits[0]["_score"] or 1.0

    notes = []
    for hit in hits:
        src = hit["_source"]
        highlights = hit.get("highlight", {}).get("text", [])
        notes.append(
            RetrievedNote(
                doc_id=src.get("doc_id", hit["_id"]),
                source_row_id=src.get("source_row_id", 0),
                subject_id=src["subject_id"],
                hadm_id=src.get("hadm_id"),
                chartdate=src.get("chartdate"),
                category=src.get("category", ""),
                highlights=highlights,
                bm25_score=hit["_score"] / max_score,  # normalize to [0, 1]
            )
        )

    return notes
