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
