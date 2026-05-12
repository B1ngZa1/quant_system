"""认证 API 集成测试"""

import pytest
from fastapi.testclient import TestClient


class TestRegister:
    def test_register_new_user_success(self, client: TestClient):
        resp = client.post("/api/v1/auth/register", json={
            "username": "newuser",
            "email": "new@example.com",
            "password": "securepassword123",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["data"]["username"] == "newuser"
        assert data["data"]["email"] == "new@example.com"
        assert "id" in data["data"]

    def test_register_duplicate_username_fails(self, client: TestClient, test_user: dict):
        resp = client.post("/api/v1/auth/register", json={
            "username": test_user["username"],
            "email": "different@example.com",
            "password": "securepassword123",
        })
        assert resp.status_code == 400

    def test_register_duplicate_email_fails(self, client: TestClient, test_user: dict):
        resp = client.post("/api/v1/auth/register", json={
            "username": "different_user",
            "email": "test@example.com",
            "password": "securepassword123",
        })
        assert resp.status_code == 400

    def test_register_creates_active_user(self, client: TestClient):
        resp = client.post("/api/v1/auth/register", json={
            "username": "activecheck",
            "email": "active@example.com",
            "password": "securepassword123",
        })
        assert resp.status_code == 200
        assert resp.json()["data"]["is_active"] is True


class TestLogin:
    def test_login_success(self, client: TestClient, test_user: dict):
        resp = client.post("/api/v1/auth/login", json={
            "username": test_user["username"],
            "password": test_user["password"],
        })
        assert resp.status_code == 200
        data = resp.json()
        assert "access_token" in data["data"]
        assert "refresh_token" in data["data"]
        assert data["data"]["token_type"] == "bearer"

    def test_login_wrong_password(self, client: TestClient, test_user: dict):
        resp = client.post("/api/v1/auth/login", json={
            "username": test_user["username"],
            "password": "wrongpassword",
        })
        assert resp.status_code == 401

    def test_login_nonexistent_user(self, client: TestClient):
        resp = client.post("/api/v1/auth/login", json={
            "username": "nobody",
            "password": "whatever",
        })
        assert resp.status_code == 401

    def test_login_by_email(self, client: TestClient, test_user: dict):
        resp = client.post("/api/v1/auth/login", json={
            "username": "test@example.com",
            "password": test_user["password"],
        })
        assert resp.status_code == 200

    def test_login_returns_expected_token_structure(self, client: TestClient, test_user: dict):
        resp = client.post("/api/v1/auth/login", json={
            "username": test_user["username"],
            "password": test_user["password"],
        })
        data = resp.json()["data"]
        assert len(data["access_token"]) > 20
        assert len(data["refresh_token"]) > 20
        assert "expires_in" in data


class TestRefreshToken:
    def test_refresh_with_valid_token(self, client: TestClient, test_user: dict):
        login_resp = client.post("/api/v1/auth/login", json={
            "username": test_user["username"],
            "password": test_user["password"],
        })
        refresh_token = login_resp.json()["data"]["refresh_token"]

        resp = client.post("/api/v1/auth/refresh", json={
            "refresh_token": refresh_token,
        })
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert "access_token" in data
        assert "refresh_token" in data
        # Token rotation: new refresh should differ from old
        assert data["refresh_token"] != refresh_token

    def test_refresh_with_invalid_token(self, client: TestClient):
        resp = client.post("/api/v1/auth/refresh", json={
            "refresh_token": "invalid-refresh-token-xxxxx",
        })
        assert resp.status_code == 401

    def test_refresh_with_short_token(self, client: TestClient):
        resp = client.post("/api/v1/auth/refresh", json={
            "refresh_token": "short",
        })
        assert resp.status_code == 422


class TestCurrentUser:
    def test_get_current_user_with_valid_token(self, client: TestClient, auth_headers: dict):
        resp = client.get("/api/v1/auth/me", headers=auth_headers)
        assert resp.status_code == 200
        assert resp.json()["data"]["username"] == "testuser"

    def test_get_current_user_without_token(self, client: TestClient):
        resp = client.get("/api/v1/auth/me")
        assert resp.status_code == 401  # 无认证头返回401

    def test_get_current_user_with_bad_token(self, client: TestClient):
        resp = client.get("/api/v1/auth/me", headers={
            "Authorization": "Bearer invalid.token.here"
        })
        assert resp.status_code == 401


class TestLogout:
    def test_logout_success(self, client: TestClient, auth_headers: dict, test_user: dict):
        login_resp = client.post("/api/v1/auth/login", json={
            "username": test_user["username"],
            "password": test_user["password"],
        })
        refresh_token = login_resp.json()["data"]["refresh_token"]

        resp = client.post("/api/v1/auth/logout", json={
            "refresh_token": refresh_token,
        }, headers=auth_headers)
        assert resp.status_code == 200
        assert resp.json()["data"]["logged_out"] is True

    def test_logout_without_token_fails(self, client: TestClient):
        resp = client.post("/api/v1/auth/logout", json={})
        assert resp.status_code in (401, 403)  # 无认证头返回401或403

    @pytest.mark.skip(reason="Requires Redis for token blacklist - skipped in test env")
    def test_refresh_after_logout_fails(self, client: TestClient, test_user: dict):
        # Login
        login_resp = client.post("/api/v1/auth/login", json={
            "username": test_user["username"],
            "password": test_user["password"],
        })
        refresh_token = login_resp.json()["data"]["refresh_token"]
        access_token = login_resp.json()["data"]["access_token"]

        # Logout
        client.post("/api/v1/auth/logout", json={
            "refresh_token": refresh_token,
        }, headers={"Authorization": f"Bearer {access_token}"})

        # Refresh after logout should fail (token revoked)
        resp = client.post("/api/v1/auth/refresh", json={
            "refresh_token": refresh_token,
        })
        assert resp.status_code == 401
