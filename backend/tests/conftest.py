"""Test fixtures (PLAN §7, Infrastructure).

- Unit tests (tests/unit) need no database.
- Integration and API tests use a separate `app_test` database named by TEST_DATABASE_URL.
  It is created if missing and migrated with Alembic once per session (never create_all),
  so the migrations themselves are tested on every run.
- Isolation: mutable tables are truncated after each test. Reference data (zones, towns,
  fares, buses) is seeded once. One mechanism for everything, because the concurrency tests
  need real commits on separate connections.
"""

import argparse
from collections.abc import Iterator
from pathlib import Path

import psycopg
import pytest
from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient
from psycopg import sql
from sqlalchemy import Engine, create_engine, make_url, text
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import settings
from app.core.db import get_session
from app.main import app
from app.models import Base
from app.seed import insert_buses, upsert_reference_data

BACKEND_DIR = Path(__file__).resolve().parents[1]
REFERENCE_TABLES = {"zones", "towns", "zone_fares", "buses"}
DB_TEST_DIRS = ("integration", "api")


def pytest_collection_modifyitems(items: list[pytest.Item]) -> None:
    if settings.TEST_DATABASE_URL is not None:
        return
    skip = pytest.mark.skip(
        reason="TEST_DATABASE_URL is not set; add it to the root .env (see CLAUDE.md)"
    )
    for item in items:
        if any(f"/tests/{d}/" in str(item.path) for d in DB_TEST_DIRS):
            item.add_marker(skip)


def _test_url() -> str:
    assert settings.TEST_DATABASE_URL is not None
    return str(settings.TEST_DATABASE_URL)


def _create_database_if_missing(url: str) -> None:
    target = make_url(url)
    admin = target.set(drivername="postgresql", database="postgres")
    with psycopg.connect(
        admin.render_as_string(hide_password=False), autocommit=True
    ) as conn:
        exists = conn.execute(
            "SELECT 1 FROM pg_database WHERE datname = %s", (target.database,)
        ).fetchone()
        if not exists:
            conn.execute(
                sql.SQL("CREATE DATABASE {}").format(sql.Identifier(target.database))
            )


def _migrate(url: str) -> None:
    cfg = Config(str(BACKEND_DIR / "alembic.ini"))
    cfg.set_main_option("script_location", str(BACKEND_DIR / "app" / "alembic"))
    cfg.cmd_opts = argparse.Namespace(x=[f"db_url={url}"])
    command.upgrade(cfg, "head")


@pytest.fixture(scope="session")
def engine() -> Iterator[Engine]:
    url = _test_url()
    _create_database_if_missing(url)
    _migrate(url)
    # Big enough pool for the concurrency tests: one connection per thread.
    eng = create_engine(url, pool_size=30, max_overflow=10, pool_pre_ping=True)
    with Session(eng) as session:
        upsert_reference_data(session)
        insert_buses(session, overwrite=True)
        session.commit()
    yield eng
    eng.dispose()


@pytest.fixture(scope="session")
def session_factory(engine: Engine) -> sessionmaker[Session]:
    return sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


def _truncate_mutable(engine: Engine) -> None:
    names = [
        t.name for t in Base.metadata.sorted_tables if t.name not in REFERENCE_TABLES
    ]
    quoted = ", ".join(engine.dialect.identifier_preparer.quote(n) for n in names)
    with engine.begin() as conn:
        # Table names come from our own metadata, never from input.
        conn.execute(text(f"TRUNCATE {quoted} RESTART IDENTITY CASCADE"))
    # Buses are reference data but tests edit them; restore the seed values.
    with Session(engine) as session:
        insert_buses(session, overwrite=True)
        session.execute(text("DELETE FROM buses WHERE plate_number NOT LIKE 'TEST-%'"))
        session.commit()


@pytest.fixture
def db(engine: Engine, session_factory: sessionmaker[Session]) -> Iterator[Session]:
    """A session on the test database. Everything it commits is wiped after the test."""
    with session_factory() as session:
        yield session
    _truncate_mutable(engine)


@pytest.fixture
def client(
    engine: Engine, session_factory: sessionmaker[Session]
) -> Iterator[TestClient]:
    def _session() -> Iterator[Session]:
        with session_factory() as session:
            yield session

    app.dependency_overrides[get_session] = _session
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
    _truncate_mutable(engine)
