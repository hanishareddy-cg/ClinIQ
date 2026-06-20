from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.db.session import Base, engine
from backend.es.client import get_es_client
from backend.es.index_setup import ensure_index


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    es = get_es_client()
    await ensure_index(es)

    yield

    await es.close()


app = FastAPI(
    title="ClinIQ API",
    description="Clinical Record Intelligence Platform — vectorless RAG over patient records",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

from backend.api.routes import health, patients, query  # noqa: E402

app.include_router(health.router, prefix="/api/v1", tags=["health"])
app.include_router(patients.router, prefix="/api/v1", tags=["patients"])
app.include_router(query.router, prefix="/api/v1", tags=["query"])
