"""Pytest 启动前设置环境变量，确保使用 PostgreSQL 测试库。"""

import os
import asyncio

import pytest
import pytest_asyncio

os.environ.setdefault("ENVIRONMENT", "development")
os.environ.setdefault("SECRET_KEY", "pytest-secret-key-minimum-32-characters-long")
os.environ.setdefault("CORS_ORIGINS", '["http://localhost:3000"]')
os.environ.setdefault("POSTGRES_DB", "quant_test_db")

_engine = None


def _get_engine():
    global _engine
    if _engine is None:
        from sqlalchemy.ext.asyncio import create_async_engine
        from app.core.config import settings
        _engine = create_async_engine(settings.postgres_url, echo=False)
    return _engine


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="session", autouse=True)
async def _create_tables():
    engine = _get_engine()
    from app.db.base import Base
    import app.models  # noqa: F401
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest.fixture()
def client():
    from fastapi.testclient import TestClient
    from sqlalchemy.ext.asyncio import AsyncSession
    from app.main import app
    from app.db.session import get_db

    engine = _get_engine()

    async def _override():
        session = AsyncSession(engine, expire_on_commit=False, autoflush=False)
        try:
            yield session
            await session.commit()
        finally:
            await session.rollback()
            await session.close()

    app.dependency_overrides[get_db] = _override
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture()
def test_user(client) -> dict:
    """Register a test user through the API and return credentials."""
    resp = client.post("/api/v1/auth/register", json={
        "username": "testuser",
        "email": "test@example.com",
        "password": "testpassword123",
    })
    if resp.status_code != 200:
        raise RuntimeError(f"Failed to create test user: {resp.json()}")
    return {"id": resp.json()["data"]["id"], "username": "testuser", "password": "testpassword123"}


@pytest_asyncio.fixture(autouse=True)
async def _cleanup_after_test():
    """Clean up test data between tests."""
    yield
    engine = _get_engine()
    from sqlalchemy.ext.asyncio import AsyncSession
    from app.models.user import User
    from app.models.trade import Trade, Portfolio, Position, PortfolioPerformance
    from app.models.strategy import Strategy
    from app.models.backtest import Backtest
    async with AsyncSession(engine, expire_on_commit=False) as session:
        async with session.begin():
            for model in [Trade, Position, PortfolioPerformance, Portfolio, Backtest, Strategy, User]:
                await session.execute(model.__table__.delete())
            await session.commit()


@pytest_asyncio.fixture()
async def db_session():
    """Per-test session for direct DB tests."""
    from sqlalchemy.ext.asyncio import AsyncSession
    engine = _get_engine()
    session = AsyncSession(engine, expire_on_commit=False, autoflush=False)
    await session.begin()
    try:
        yield session
        await session.commit()
    finally:
        await session.rollback()
        await session.close()


@pytest.fixture()
def auth_headers(client, test_user: dict) -> dict:
    """Login and return auth headers."""
    resp = client.post("/api/v1/auth/login", json={
        "username": test_user["username"],
        "password": test_user["password"],
    })
    data = resp.json()
    token = data["data"]["access_token"]
    return {"Authorization": f"Bearer {token}"}
