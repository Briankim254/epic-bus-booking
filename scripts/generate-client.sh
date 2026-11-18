#! /usr/bin/env bash
# Dump the backend's OpenAPI schema and regenerate the typed frontend client.
set -e
set -x

cd "$(dirname "$0")/.."
(cd backend && uv run python -c "import app.main, json; print(json.dumps(app.main.app.openapi()))") > frontend/openapi.json
yarn workspace frontend generate-client
yarn workspace frontend lint
