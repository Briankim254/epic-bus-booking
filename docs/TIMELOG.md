# Time log

Hours count from Saturday 14 November 2026. All times are EAT (UTC+3).

Where a row has start and end times, they come from evidence: commit timestamps. Rows marked _to fill_ are work done away from the repo (reading, planning on paper, reviewing). Their hours come from my own record.

## Summary

| Area | Hours | Share |
|---|---|---|
| Planning (brief, build plan, repo, backend and frontend plans) | 3.1| |
| API development (skeleton, models, migrations, seed, domain, services, routes, tests) | 5.15 | |
| Frontend | 1.9 | |
| Docs and review | 3.25 | |
| **Total** | **13.4** | |

## Log

| Date | Start | End | Hours | Area | What |
|---|---|---|---|---|---|
| Sat 14 Nov | | | ~1 hr | Planning | Read the brief. Listed what it settles and what it leaves open (cancellations, seats per booking, bus capacity, time zone) |
| Mon 16 Nov | | | ~2.5 hrs | Planning | Build plan, assumptions , data model and constraints, trip state machine, the overbooking design (a conditional UPDATE plus a CHECK), API and error format, idempotency, test plan, cut-line and schedule |
| Tue 17 → Wed 18 Nov | 00:15 | 00:45 | 0.5 | Planning | Monorepo plan: uv and Yarn workspaces, separate frontend service, what to copy from the recommended flask template and what to leave out |
| Tue 17 Nov | 00:45 | 01:50 | 1.1 | API development | Monorepo skeleton: compose stack, FastAPI app factory, problem+json errors, JSON logs with request ids, health check, CI, docs skeletons |
| Wed 18 Nov | 17:45 | 19:30 | 1.75 | API development | Models (zones, towns, fares, trips, bookings), initial migration (read and checked), seed command with relative departure times, reconciliation check, seed-data tests. `git init` at 19:18 |
| Wed 18 Nov | 20:10 | 21:00 | 0.8 | API development | Bus model and seed buses. Generated and applied the bus migration |
| Thu 19 Nov | 11:45 | 12:55 | 1.2 | Planning | Backend API plan: 14 endpoints, phases, test-first order, stop points for running migrations myself. Committed the models and seed (PR #1) |
| Thu 19 Nov | 13:45 | 15:15 | 1.5 | API development | Test database setup; domain errors and fares written test-first; idempotency and status-history migration; repositories, services, routes; booking and concurrency tests (last-seat race run 20 times in a row); API tests. PR #2 |
| Thu 19 Nov | 17:30 | 17:55 | 0.4 | Planning | Frontend plan: component tree, URL search state, booking and 409 handling, read-only admin table, browser walkthrough checklist |
| Thu 19 Nov | 17:55 | 19:50 | 1.9 | Frontend | Search form, results, inline booking with idempotency key, confirmation, admin trips table. Browser walkthrough found and fixed a lost-confirmation bug |
| Thu 19 Nov | | 22:35 | 0.25 | Docs and review | Reviewed the frontend and committed it |
| Fri 20 Nov | 14:15 | 15:30 | 1.25 | Docs and review | Fixed the filter-bar alignment, added a Clear button, wrote up the stack trade-offs, filled in this time log |
| Fri 20 Nov | 21:00 | 22:15 | 1.25 | Docs and review & API Development | Design document, handover note, AI disclosure summary, fresh-clone README run-through. Additional ai bug fixes |
