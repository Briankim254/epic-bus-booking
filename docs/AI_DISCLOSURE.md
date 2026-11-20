# AI use disclosure

I used AI at every stage of this project, and treated everything it produced as an unverified draft. Nothing merged until it had passed linting, static analysis, tests and my own review, and I only committed code I can explain line by line.

## Which parts were written by hand, and which were AI-assisted?

| Stage | AI-assisted | Mine |
|---|---|---|
| Design | AI drafted the build plan, data model, API design and options for each trade-off | Which assumptions to make, what to cut (Superset, Redis holds, extra filters), the read-only admin table, and the trade-offs the design document defends |
| Coding | Claude Code drafted the models, repositories, services, routes, seed command and both frontend pages | Directing each step, and reviewing every change before committing it |
| Testing | Claude Code drafted most of the tests, including edge cases and the concurrency test | Deciding what had to be proven (the last-seat race, fares, the state machine, no names in logs), and checking that each test fails for the right reason |
| Code review | Claude Code gave a first pass on lint and type errors, and on bugs it found in the browser | The final review of every diff, and the merges |
| Documentation | Claude Code turned my notes and the code into first drafts of the README, the design document and this disclosure | Editing them. Hours in the time log that weren't spent in the repo |
| Database changes | Claude Code could draft a migration and trial-run it on a throwaway database | Every migration: I generated it, read it and applied it myself |

## Which tools?

- **Claude:** the first build plan, checked against the brief.
- **Claude Code:** design, coding, tests, documentation, and checks in the browser for the frontend, on Claude Opus models in the Claude desktop app.
- **Not used:** I didn't use any other assistants on this project. I didn't copy the template's agent-skill folders (`.claude/skills`, `.agents/skills`) into this repo.

## Where I draw the line, and why

- **Credentials, secrets and production access.** The assistant never saw a real credential. `.claude/settings.json` denies it read access to `.env` and `.env.*`, and examples use obvious dummies (`postgres://app:example@db/app`). It only ever ran against my local Docker stack, never against a shared or production database, and it deployed nothing. A hallucinated command or a leaked secret can do real damage, and accountability for anything that isn't local has to stay with a person.
- **Schema changes.** A migration applied anywhere shared can't be edited afterwards. So generating, reading and applying each migration was always my step.
- **Design and security decisions.** AI suggested options, and I made the call:
  - what to build and cut
  - leaving the admin API unauthenticated (per the brief), with its own router as the place auth goes
  - validating names at the edge
  - never logging personal data

## How I handled the risks

- **Incorrect output.** I treated every output as a draft.
  - **Tests first.** The rules that matter were written test-first, failing before the code made them pass: fares, domain errors, the booking service. The 170 tests run against a real Postgres migrated by Alembic, so the migrations are tested too.
  - **The last-seat race.** A concurrency test starts 20 threads behind a barrier, all booking the same trip, then asserts no seat drift. I ran it 20 times in a row with no failures.
  - **Static checks.** mypy (strict), ruff, Biome and `tsc` all pass with no errors.
  - **Browser walkthrough.** It covered search, validation, booking, the last-seat 409 from a stale tab, the admin table and a 375px-wide screen. It caught a real bug, a confirmation that disappeared, which was then fixed.
  - **Before submitting:** a fresh-clone README run-through. _(to do)_
- **Data leakage.**
  - Prompts never held secrets or real personal data.
  - Every passenger name in the seed data is fictional.
  - The app never logs passenger names, full booking references or request bodies. A test checks that a booked name never appears in the logs.
  - Error responses never echo submitted input.
- **Security exposure.** The code that handles data got my own review even where AI wrote it: input validation and name cleaning, bound-parameter SQL, problem+json errors, and CORS. gitleaks runs as a pre-commit hook.
- **Over-reliance.** I only commit code I can explain line by line. The overbooking guard was drafted with AI: the conditional `UPDATE` in `repositories/trips.py` and the `ck_trips_seats_range` CHECK. I don't treat it as a black box. I can walk through the row-lock race, and I prove it with the concurrency test and the database CHECK as a second layer.
- **Intellectual property.** I checked generated code the way I would third-party code, looking for anything that seemed copied. Code adapted from full-stack-fastapi-template (MIT) is credited in the README, with the commit it came from.

## Running log

| Date | Task | Tool | By hand / assisted | How verified |
|---|---|---|---|---|
| 2026-11-17 | Build plan| | By Hand | |
| 2026-11-18 | Monorepo init plan and skeleton (this repo's first state) | Claude Code | Assisted | Lint, smoke tests, `docker compose up`, manual review of every file |
| 2026-11-18 | Models, initial migration, seed command, seed-data tests | | By Hand| |
| 2026-11-18 | Bus model and bus seed data (migration generated and applied by me) | Claude Code | Assisted | Unit tests; Claude trial-ran the migration and seed on a throwaway Postgres; I ran autogenerate, read the migration, upgraded and seeded myself |
| 2026-11-19 | Backend API: domain errors and fares (TDD), idempotency and status-history models, repositories, services, routes, API tests, client regen | Claude Code | Assisted (I generated and applied the migrations) | Tests written before code (red, then green); 167 tests; last-seat race run 20× in a row; lint (mypy strict, ruff); read-only smoke test on the running stack |
| 2026-11-19 | Frontend: customer search and inline booking, admin trips table; typed problem+json in OpenAPI | Claude Code | Assisted | yarn lint/build; scripted browser walkthrough (search, validation, booking, last-seat 409 from a stale second tab, admin table, 375px width, console clean); backend tests still green |
| 2026-11-20 | Filter-bar alignment fix and a Clear button (from my screenshot and request) | Claude Code | Assisted | Browser check; yarn lint/build |
| 2026-11-20 | Time log reconstructed from commit timestamps | Claude Code | Assisted (off-repo hours are mine) | Every timed row checked against `git log`; totals recomputed |
| 2026-11-20 | `seed --today` to anchor demo data to the interview day (Tue 24 Nov) | | By hand | |
| 2026-11-20 | Design document and this disclosure drafted | Claude Code | By hand, Assisted in review and proofreading | Each claim checked against the code (constraint names, log events, endpoints) |
