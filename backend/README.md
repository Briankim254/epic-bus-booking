# Backend

FastAPI + SQLAlchemy 2.0 (sync) + Alembic on PostgreSQL. Python 3.14, managed by uv.

## Run on the host

```bash
cp ../.env.example ../.env       # once, from the repo root
docker compose up -d db          # from the repo root
uv sync
uv run alembic upgrade head
uv run fastapi dev               # http://localhost:8000/docs
```

## Tests and lint

```bash
uv run bash scripts/test.sh
uv run bash scripts/lint.sh
```

## Layout

| Path | Holds |
|---|---|
| `app/api/routes/` | HTTP only: parse, call one service method, shape the response |
| `app/services/` | Orchestration and transactions |
| `app/repositories/` | All SQL |
| `app/domain/` | Pure business rules (fares, trip status, references). No FastAPI, no SQLAlchemy |
| `app/models/` | SQLAlchemy tables. Register every module in `models/__init__.py` |
| `app/schemas/` | Pydantic API contracts |
| `app/core/` | Settings, DB engine, problem+json errors, JSON logging |
| `app/cli.py` | `seed`, `reconcile`, `purge-idempotency` |
