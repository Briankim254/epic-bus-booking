# EPIC Booking

A prototype intercity bus booking service for six Nigerian towns in four fare zones. Customers search trips by origin, destination and date, then book seats and get a reference on the same page. Operators see a read-only list of trips and how full each one is.

## Provenance

This is a new monorepo. It is **not** a fork. Some configuration and the shadcn/ui components were adapted from [full-stack-fastapi-template](https://github.com/fastapi/full-stack-fastapi-template) at commit `77e550a`. [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md) lists every file taken from it, along with its MIT licence. Auth, users, email, Traefik, Sentry and the template's deployment setup were left out.

## Quick start

Prerequisites: Docker with Compose v2.

```bash
cp .env.example .env
docker compose up --build
```

| What | URL |
|---|---|
| Web app (customer search) | http://localhost:5173 |
| Admin trips table | http://localhost:5173/admin/trips |
| API docs (OpenAPI) | http://localhost:8000/docs |
| Adminer (server `db`, user `postgres`, password from `.env`) | http://localhost:8080 |

## Reset and reseed

```bash
docker compose down -v && docker compose up -d --build
```

The `prestart` service runs `alembic upgrade head` and then `python -m app.cli seed` on every start. Seed departure times are relative to now, so there are always future trips.

## Run the tests

```bash
docker compose up -d db
uv sync --all-packages
cd backend && uv run bash scripts/test.sh
```

Lint everything: `cd backend && uv run bash scripts/lint.sh` and `yarn lint`.

## Example: price a journey, book a seat


```bash

```

## Main entry points

| Area | File |
|---|---|
| API app factory | [backend/app/main.py](backend/app/main.py) |
| Booking transaction | `backend/app/services/booking_service.py` |
| Fare rules | `backend/app/domain/fares.py` |
| Trip state machine | `backend/app/domain/trip_status.py` |
| Customer page | [frontend/src/routes/index.tsx](frontend/src/routes/index.tsx) |
| Admin table | [frontend/src/routes/admin/trips.tsx](frontend/src/routes/admin/trips.tsx) |

## Assumptions

| # | Assumption |
|---|---|
| A1 | Only `Scheduled` trips with a future departure can be booked |
| A2 | Origin and destination must be different towns. Lagos → Ibadan is a valid same-zone journey at $8 |
| A3 | The search date is a calendar day in Africa/Lagos. Times are stored in UTC |
| A4 | The fare is per seat. A booking's total is seats × fare, fixed at booking time |
| A5 | At most 10 seats per booking, and never more than remain |
| A6 | Bookings and trips cannot be cancelled |
| A7 | Trip status changes are an operator action through the API. The dashboard is read-only, as specified |
| A8 | Seats are a count per trip, not numbered |

## Repository layout

```text
backend/     FastAPI + SQLAlchemy 2.0 + Alembic (uv workspace member)
frontend/    React + Vite + TanStack + shadcn/ui (yarn workspace)
docs/        DESIGN, HANDOVER, AI_DISCLOSURE, TIMELOG, PLAN
scripts/     generate-client.sh, reset-db.sh
compose.yml  db, adminer, prestart, backend, frontend
```

## More documents

- [Design document](docs/DESIGN.md)
- [Handover note](docs/HANDOVER.md)
- [AI use disclosure](docs/AI_DISCLOSURE.md)
- [Time log](docs/TIMELOG.md)
