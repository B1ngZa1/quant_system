from typing import Any, Dict, Tuple

import requests


BASE = "http://127.0.0.1:8000"


def _sample_body(path: str, method: str) -> Dict[str, Any]:
    if path in ("/api/v1/auth/register", "/api/v1/auth/create"):
        return {
            "username": "smoke_user_001",
            "email": "smoke_user_001@example.com",
            "password": "123456",
        }
    if path in ("/api/v1/auth/login", "/api/v1/auth/action"):
        return {"username": "smoke_user_001", "password": "123456"}
    if path in ("/api/v1/auth/refresh", "/api/v1/auth/update"):
        return {"refresh_token": "invalid_refresh_token_for_smoke"}
    if path in ("/api/v1/auth/logout", "/api/v1/auth/remove"):
        return {"refresh_token": "invalid_refresh_token_for_smoke"}
    return {}


def _materialize_path(path: str) -> str:
    # 使用稳定占位符，避免误删真实数据
    return (
        path.replace("{user_id}", "1")
        .replace("{strategy_id}", "1")
        .replace("{backtest_id}", "1")
        .replace("{portfolio_id}", "1")
        .replace("{trade_id}", "1")
        .replace("{symbol}", "000001")
        .replace("{capability}", "default")
        .replace("{action_name}", "run")
    )


def _run() -> Tuple[int, int, int]:
    openapi = requests.get(f"{BASE}/openapi.json", timeout=15).json()
    paths = openapi.get("paths", {})

    # 先注册+登录拿 token
    requests.post(f"{BASE}/api/v1/auth/register", json=_sample_body("/api/v1/auth/register", "post"), timeout=15)
    login_resp = requests.post(
        f"{BASE}/api/v1/auth/login",
        json=_sample_body("/api/v1/auth/login", "post"),
        timeout=15,
    )
    token = None
    if login_resp.status_code == 200:
        data = login_resp.json().get("data", {})
        token = data.get("access_token")

    tested = 0
    server_errors = 0
    route_errors = 0

    for path, methods in paths.items():
        for method, _meta in methods.items():
            m = method.lower()
            if m not in {"get", "post", "put", "patch", "delete"}:
                continue

            url = f"{BASE}{_materialize_path(path)}"
            headers = {}
            if token:
                headers["Authorization"] = f"Bearer {token}"

            body = _sample_body(path, m)
            try:
                if m == "get":
                    resp = requests.get(url, headers=headers, timeout=20)
                elif m == "post":
                    resp = requests.post(url, json=body, headers=headers, timeout=20)
                elif m == "put":
                    resp = requests.put(url, json=body, headers=headers, timeout=20)
                elif m == "patch":
                    resp = requests.patch(url, json=body, headers=headers, timeout=20)
                else:
                    resp = requests.delete(url, json=body, headers=headers, timeout=20)
            except Exception:
                route_errors += 1
                tested += 1
                continue

            if resp.status_code >= 500:
                server_errors += 1
            if resp.status_code == 404:
                route_errors += 1
            tested += 1

            print(f"{m.upper():<6} {path:<45} -> {resp.status_code}")

    print("\n==== SUMMARY ====")
    print(f"tested={tested}")
    print(f"server_errors={server_errors}")
    print(f"route_errors={route_errors}")
    return tested, server_errors, route_errors


if __name__ == "__main__":
    _run()
