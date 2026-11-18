#! /usr/bin/env bash
# Wipe the database volume and start fresh: migrations and seed run again in `prestart`.
set -e
set -x

cd "$(dirname "$0")/.."
docker compose down -v --remove-orphans
docker compose up -d --build
