from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_endpoint_returns_healthy_status():
    response = client.get("/health")
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "healthy"
    assert "version" in payload


def test_root_endpoint_contains_basic_metadata():
    response = client.get("/")
    assert response.status_code == 200
    payload = response.json()
    assert "name" in payload
    assert "api" in payload
