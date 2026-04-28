import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest.mark.asyncio
async def test_prometheus_metrics():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Generate some traffic to ensure metrics are recorded
        await client.get("/health")

        # Fetch metrics
        response = await client.get("/metrics")
        assert response.status_code == 200

        content = response.text
        # Check that prometheus format is returned
        assert "http_requests_total" in content or "http_requests_inprogress" in content
        # Check that our request to /health was captured
        assert 'handler="/health"' in content or 'status="200"' in content
