from fastapi.testclient import TestClient

from app.main import app


def test_openapi_contains_required_routes() -> None:
    client = TestClient(app)
    routes = client.get("/openapi.json").json()["paths"]
    for path in [
        "/health",
        "/auth/register",
        "/auth/login",
        "/auth/token",
        "/auth/logout",
        "/auth/me",
        "/documents/upload",
        "/documents/{document_id}/process",
        "/chat/query",
        "/review/items",
        "/evals/run",
        "/admin/audit-logs",
        "/admin/analytics",
    ]:
        assert path in routes


def test_cookie_authenticated_mutation_requires_allowlisted_origin() -> None:
    client = TestClient(app)
    response = client.post("/auth/logout", cookies={"knowledge_session": "untrusted"})
    assert response.status_code == 403


def test_cookie_authenticated_mutation_accepts_configured_origin() -> None:
    client = TestClient(app)
    response = client.post(
        "/auth/logout",
        cookies={"knowledge_session": "untrusted"},
        headers={"Origin": "http://localhost:3000"},
    )
    assert response.status_code == 204
