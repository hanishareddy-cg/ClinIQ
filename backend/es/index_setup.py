from elasticsearch import AsyncElasticsearch

from backend.config import get_settings

NOTES_INDEX_MAPPING = {
    "settings": {
        "number_of_shards": 1,
        "number_of_replicas": 0,
        "analysis": {
            "filter": {
                "clinical_stop": {
                    "type": "stop",
                    "stopwords": [
                        "the", "a", "an", "is", "was", "were", "be", "been",
                        "being", "have", "has", "had", "do", "does", "did",
                        "will", "would", "could", "should",
                    ],
                    # medical terms like "normal", "negative" are intentionally kept
                }
            },
            "analyzer": {
                "clinical_analyzer": {
                    "type": "custom",
                    "tokenizer": "standard",
                    "filter": ["lowercase", "clinical_stop"],
                    # no stemming: "creatinine" != "creatinin" in clinical context
                }
            },
        },
    },
    "mappings": {
        "properties": {
            "doc_id":       {"type": "keyword"},
            "subject_id":   {"type": "integer"},
            "hadm_id":      {"type": "integer"},
            "chartdate":    {"type": "date", "format": "yyyy-MM-dd"},
            "category":     {"type": "keyword"},
            "description":  {"type": "keyword"},
            "text": {
                "type": "text",
                "analyzer": "clinical_analyzer",
                "term_vector": "with_positions_offsets",
                "fields": {
                    "raw": {"type": "keyword", "ignore_above": 256}
                },
            },
            "chunk_index":   {"type": "integer"},
            "chunk_total":   {"type": "integer"},
            "source_row_id": {"type": "integer"},
        }
    },
}


async def ensure_index(es: AsyncElasticsearch) -> None:
    settings = get_settings()
    index_name = settings.es_index
    exists = await es.indices.exists(index=index_name)
    if not exists:
        await es.indices.create(index=index_name, body=NOTES_INDEX_MAPPING)
