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

## Seed data, reset and reseed

On every start, the `prestart` service runs `alembic upgrade head` and then `python -m app.cli seed` ([backend/app/seed.py](backend/app/seed.py)). The seed contains:

- 6 towns in 4 zones and the 10-row fare table. These are upserted on every run.
- 4 buses with dummy plates `TEST-001` to `TEST-004`: two with 44 seats, two with 40. Missing buses are added on every run, but existing ones are never overwritten, so an operator's edits survive a restart.
- 10 trips, each assigned a bus and copying its capacity (40 or 44). Eight are `scheduled` over the next three days, one is `departed` (on the road now) and one is `arrived`. Departure times are relative to now, so there are always future trips.
- 15 bookings. Lagos → Abuja tomorrow is left with **exactly one seat** for the last-seat demo.

Trips and bookings are only inserted when the `trips` table is empty, so restarting never duplicates them. Every counter is checked against the bookings at the end of a seed run.

```bash
# Reseed trips and bookings and restore the seed buses, keeping the database
docker compose exec backend python -m app.cli seed --reset

# Full reset: drop the database volume, then migrate and seed from scratch
docker compose down -v && docker compose up -d --build

# Check seat counters against bookings (exits non-zero on drift)
docker compose exec backend python -m app.cli reconcile
```

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
| A9 | Every trip runs on one bus. The trip copies the bus's capacity when the bus is assigned, so a later capacity change only affects trips assigned after it |
| A10 | A trip can move to another bus only while `Scheduled`, and only if the new bus is active and has at least as many seats as are already booked |
| A11 | Bus editing is an operator action through the unauthenticated admin API, the same as trip status changes |

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
