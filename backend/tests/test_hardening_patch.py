import pytest
from unittest.mock import patch

from app.db import session as session_module
from app.core.config import Settings
from app.services.data_engine import DataEngineService


@pytest.mark.asyncio
@patch(
    "app.services.data_engine.load_market_quotes_from_latest_panel",
    lambda *a, **k: ([], 0),
)
async def test_data_engine_quotes_payload_keeps_rows_and_items_contract():
    service = DataEngineService()

    async def _not_fresh(db):
        return False

    async def _none_ak(*args, **kwargs):
        return None

    service._is_db_realtime_fresh = _not_fresh  # type: ignore[method-assign]
    service._try_akshare_quotes = _none_ak  # type: ignore[method-assign]

    payload = await service.get_quotes(
        page=1,
        page_size=20,
        search=None,
        exchange=None,
        industry=None,
        db=None,  # not used because freshness/ak are monkeypatched
        cache=None,
    )

    assert "rows" in payload
    assert "items" in payload
    assert payload["rows"] == payload["items"]
    assert payload["total"] == len(payload["rows"])
    assert payload["source"] == "unavailable"


@pytest.mark.asyncio
async def test_get_db_dependency_does_not_auto_commit():
    class FakeSession:
        def __init__(self):
            self.committed = 0
            self.rolled_back = 0
            self.closed = 0

        async def commit(self):
            self.committed += 1

        async def rollback(self):
            self.rolled_back += 1

        async def close(self):
            self.closed += 1

    class FakeSessionContext:
        def __init__(self, session):
            self._session = session

        async def __aenter__(self):
            return self._session

        async def __aexit__(self, exc_type, exc, tb):
            return False

    fake_session = FakeSession()
    original_factory = session_module.AsyncSessionLocal
    session_module.AsyncSessionLocal = lambda: FakeSessionContext(fake_session)
    try:
        gen = session_module.get_db()
        yielded = await gen.__anext__()
        assert yielded is fake_session

        with pytest.raises(StopAsyncIteration):
            await gen.__anext__()

        assert fake_session.committed == 0
        assert fake_session.rolled_back == 0
        assert fake_session.closed == 1
    finally:
        session_module.AsyncSessionLocal = original_factory


def test_cors_origins_parsing_from_string():
    s = Settings(CORS_ORIGINS="https://a.example.com, https://b.example.com")
    assert s.CORS_ORIGINS == ["https://a.example.com", "https://b.example.com"]


def test_production_requires_cors_origins():
    with pytest.raises(ValueError):
        Settings(
            ENVIRONMENT="production",
            SECRET_KEY="x" * 32,
            POSTGRES_PASSWORD="strong-password",
            CORS_ORIGINS=[],
            _env_file=None,
        )


def test_production_disallows_localhost_origins():
    with pytest.raises(ValueError):
        Settings(
            ENVIRONMENT="production",
            SECRET_KEY="x" * 32,
            POSTGRES_PASSWORD="strong-password",
            CORS_ORIGINS=["http://localhost:3000"],
            _env_file=None,
        )
