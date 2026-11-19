from typing import Any

from app.core.errors import Problem

_DESCRIPTIONS = {
    404: "Not found",
    409: "Conflict with the current state",
    422: "Invalid request",
}


def problems(*codes: int) -> dict[int | str, dict[str, Any]]:
    """OpenAPI entries so the generated client gets typed problem+json errors."""
    return {
        c: {
            "model": Problem,
            "description": _DESCRIPTIONS[c],
            "content": {"application/problem+json": {}},
        }
        for c in codes
    }
