# Build context: repository root (the uv workspace lockfile lives there)
FROM python:3.14-slim

ENV PYTHONUNBUFFERED=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    PATH="/app/.venv/bin:$PATH"

COPY --from=ghcr.io/astral-sh/uv:0.13.9 /uv /uvx /bin/

WORKDIR /app/

# Dependencies first, for layer caching
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    --mount=type=bind,source=backend/pyproject.toml,target=backend/pyproject.toml \
    uv sync --frozen --no-install-workspace --package app

COPY ./backend/scripts /app/backend/scripts
COPY ./backend/pyproject.toml ./backend/alembic.ini /app/backend/
COPY ./backend/app /app/backend/app

RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --frozen --package app

WORKDIR /app/backend/

CMD ["fastapi", "run", "--host", "0.0.0.0", "--port", "8000"]
