# AI use disclosure

## Which parts were written by hand, and which were AI-assisted?

<!-- Summarise from the log below at the end. -->

## Which tools?

<!-- e.g. Claude Code (model), editor assistants. Template agent-skill folders were not copied into this repo. -->

## How was AI output verified?

<!-- Tests written before code for fares and booking; every migration read; concurrency test run repeatedly; fresh-clone README run. -->

## Where was AI deliberately not used, and why?

<!-- e.g. the conditional seat UPDATE, the booking transaction and the last-seat concurrency test. -->

## Running log

Add a row as you go. Reconstructing this on Friday night will be inaccurate.

| Date | Task | Tool | By hand / assisted | How verified |
|---|---|---|---|---|
| 2026-11-17 | Build plan (PLAN 1.md) | Claude | Assisted | Read against the brief; assumptions checked |
| 2026-11-18 | Monorepo init plan and skeleton (this repo's first state) | Claude Code | Assisted | Lint, smoke tests, `docker compose up`, manual review of every file |
| 2026-11-18 | Models, initial migration, seed command, seed-data tests | Claude Code | Assisted | Read the migration; seeded twice (idempotent) and with --reset; reconcile clean; queried rows against the brief |
| 2026-11-18 | Bus model and bus seed data (migration generated and applied by me) | Claude Code | Assisted | Unit tests; Claude trial-ran the migration and seed on a throwaway Postgres; I ran autogenerate, read the migration, upgraded and seeded myself |
| 2026-11-19 | Backend API: domain errors and fares (TDD), idempotency and status-history models, repositories, services, routes, API tests, client regen | Claude Code | Assisted (I generated and applied the migrations) | Tests written before code (red, then green); 167 tests; last-seat race run 20× in a row; lint (mypy strict, ruff); read-only smoke test on the running stack |
| 2026-11-19 | Frontend: customer search and inline booking, admin trips table; typed problem+json in OpenAPI | Claude Code | Assisted | yarn lint/build; scripted browser walkthrough (search, validation, booking, last-seat 409 from a stale second tab, admin table, 375px width, console clean); backend tests still green |
