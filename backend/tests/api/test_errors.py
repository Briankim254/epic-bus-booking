from collections.abc import Iterator

import pytest
from fastapi import APIRouter
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def boom_client(client: TestClient) -> Iterator[TestClient]:
    del client  # only for its DB override and cleanup
    router = APIRouter(tags=["health"])

    @router.get("/api/v1/__boom", include_in_schema=False)
    def boom() -> None:
        raise RuntimeError("secret internal detail")

    app.include_router(router)
    try:
        with TestClient(app, raise_server_exceptions=False) as c:
            yield c
    finally:
        app.router.routes[:] = [
            r for r in app.router.routes if getattr(r, "path", "") != "/api/v1/__boom"
        ]


def test_unhandled_error_is_a_generic_500_problem(boom_client: TestClient) -> None:
    r = boom_client.get("/api/v1/__boom")
    assert r.status_code == 500
    assert r.headers["content-type"].startswith("application/problem+json")
    body = r.json()
    assert body["code"] == "internal-error"
    assert body["request_id"] == r.headers["X-Request-ID"]
    assert "secret internal detail" not in r.text
