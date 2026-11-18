from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

from app.main import app

# Wednesday: create `app_test` if missing, run `alembic upgrade head` against it once per
# session, override get_session, and TRUNCATE mutable tables after each test (PLAN §7).


@pytest.fixture(scope="module")
def client() -> Iterator[TestClient]:
    with TestClient(app) as c:
        yield c
