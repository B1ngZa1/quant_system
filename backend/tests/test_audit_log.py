import pytest
from starlette.requests import Request

from app.models.user import User
from app.utils import audit_log as audit_log_module
from app.utils.audit_log import audit_log, write_audit_log


class _FakeSession:
    def __init__(self):
        self.added = []
        self.committed = 0

    def add(self, obj):
        self.added.append(obj)

    async def commit(self):
        self.committed += 1


class _FakeSessionContext:
    def __init__(self, session):
        self._session = session

    async def __aenter__(self):
        return self._session

    async def __aexit__(self, exc_type, exc, tb):
        return False


def _make_request(path: str = "/api/v1/trade/order", method: str = "POST") -> Request:
    scope = {
        "type": "http",
        "method": method,
        "path": path,
        "headers": [(b"user-agent", b"pytest")],
        "client": ("127.0.0.1", 12345),
        "scheme": "http",
        "server": ("testserver", 80),
        "query_string": b"",
        "root_path": "",
        "http_version": "1.1",
    }
    return Request(scope)


@pytest.mark.asyncio
async def test_audit_log_recorded_for_trade(monkeypatch):
    fake = _FakeSession()
    monkeypatch.setattr(audit_log_module, "AsyncSessionLocal", lambda: _FakeSessionContext(fake))

    req = _make_request()
    await write_audit_log(
        user=None,
        action="下单",
        resource="trade",
        request=req,
        success=True,
        status_code=200,
        detail={"symbol": "000001.SZ"},
    )

    assert fake.committed == 1
    assert len(fake.added) == 1
    row = fake.added[0]
    assert row.action == "下单"
    assert row.resource == "trade"
    assert row.method == "POST"
    assert row.path == "/api/v1/trade/order"
    assert row.ip == "127.0.0.1"
    assert row.success is True


@pytest.mark.asyncio
async def test_audit_log_decorator_records_logout(monkeypatch):
    fake = _FakeSession()
    monkeypatch.setattr(audit_log_module, "AsyncSessionLocal", lambda: _FakeSessionContext(fake))

    user = User(username="u", email="u@example.com", hashed_password="x")
    req = _make_request(path="/api/v1/auth/logout", method="POST")

    @audit_log(action="登出", resource="auth", detail_builder=lambda **_: {"reason": "manual"})
    async def _logout(request: Request, _current_user: User):
        return {"ok": True}

    result = await _logout(request=req, _current_user=user)
    assert result == {"ok": True}
    assert fake.committed == 1
    assert fake.added[0].action == "登出"
    assert fake.added[0].resource == "auth"

