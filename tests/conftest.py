from contextlib import asynccontextmanager
from unittest.mock import AsyncMock

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from backend.db.session import Base
from backend.dependencies import get_db, get_es


@pytest.fixture
async def db_session():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with session_factory() as session:
        yield session
    await engine.dispose()


@pytest.fixture
def mock_es():
    es = AsyncMock()
    es.ping.return_value = True
    es.search.return_value = {
        "hits": {
            "total": {"value": 0},
            "hits": [],
        }
    }
    return es


@pytest.fixture
async def async_client(db_session, mock_es):
    import backend.main as _main

    @asynccontextmanager
    async def _noop_lifespan(app):
        yield

    original_lifespan = _main.app.router.lifespan_context
    _main.app.router.lifespan_context = _noop_lifespan

    async def override_db():
        yield db_session

    async def override_es():
        return mock_es

    _main.app.dependency_overrides[get_db] = override_db
    _main.app.dependency_overrides[get_es] = override_es

    async with AsyncClient(
        transport=ASGITransport(app=_main.app), base_url="http://test"
    ) as client:
        yield client

    _main.app.router.lifespan_context = original_lifespan
    _main.app.dependency_overrides.clear()
