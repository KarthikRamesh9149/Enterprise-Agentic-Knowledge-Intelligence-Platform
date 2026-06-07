from fastapi.testclient import TestClient

from app.main import app


def test_openapi_contains_required_routes() -> None:
    client = TestClient(app)
    routes = client.get("/openapi.json").json()["paths"]
    for path in [
        "/health",
        "/auth/register",
        "/auth/login",
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

