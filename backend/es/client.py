from functools import lru_cache

from elasticsearch import AsyncElasticsearch

from backend.config import get_settings


@lru_cache
def get_es_client() -> AsyncElasticsearch:
    settings = get_settings()
    return AsyncElasticsearch(
        hosts=[{"host": settings.es_host, "port": settings.es_port, "scheme": "http"}],
        request_timeout=30,
        retry_on_timeout=True,
        max_retries=3,
    )
