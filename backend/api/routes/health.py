from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from backend.dependencies import get_db, get_es
from backend.models.schemas import HealthResponse, ReadyResponse

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
async def health():
    return {"status": "ok"}


@router.get("/ready", response_model=ReadyResponse)
async def ready(db: AsyncSession = Depends(get_db), es=Depends(get_es)):
    pg_ok = False
    es_ok = False

    try:
        await db.execute(text("SELECT 1"))
        pg_ok = True
    except Exception:
        pass

    try:
        await es.ping()
        es_ok = True
    except Exception:
        pass

    status = "ready" if pg_ok and es_ok else "degraded"
    return {"postgres": pg_ok, "elasticsearch": es_ok, "status": status}
