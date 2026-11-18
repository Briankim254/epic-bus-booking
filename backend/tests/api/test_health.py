from fastapi.testclient import TestClient


def test_health_ok_with_request_id(client: TestClient) -> None:
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
    assert response.headers["X-Request-ID"]


def test_request_id_is_echoed(client: TestClient) -> None:
    response = client.get("/api/v1/health", headers={"X-Request-ID": "abc123"})
    assert response.headers["X-Request-ID"] == "abc123"


def test_unknown_route_is_problem_json(client: TestClient) -> None:
    response = client.get("/api/v1/does-not-exist")
    assert response.status_code == 404
    assert response.headers["content-type"].startswith("application/problem+json")
    body = response.json()
    assert body["code"] == "not-found"
    assert body["request_id"]
