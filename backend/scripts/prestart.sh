#! /usr/bin/env bash
set -e
set -x

# Apply migrations, then seed (idempotent)
alembic upgrade head
python -m app.cli seed
