"""Every error leaves the API as application/problem+json (RFC 9457)."""

import logging
from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import Response

from app.core.logging import request_id_var
from app.domain.errors import DomainError

PROBLEM_MEDIA_TYPE = "application/problem+json"
logger = logging.getLogger("app.errors")


class FieldError(BaseModel):
    field: str
    message: str


class Problem(BaseModel):
    model_config = ConfigDict(extra="allow")

    type: str
    title: str
    status: int
    detail: str | None = None
    instance: str | None = None
    code: str
    request_id: str | None = None
    errors: list[FieldError] | None = None


def problem_response(
    request: Request,
    *,
    status: int,
    code: str,
    title: str,
    detail: str | None = None,
    **extra: Any,
) -> JSONResponse:
    body = Problem(
        type=f"https://errors.local/{code}",
        title=title,
        status=status,
        detail=detail,
        instance=request.url.path,
        code=code,
        request_id=request_id_var.get(),
        **extra,
    )
    return JSONResponse(
        body.model_dump(exclude_none=True),
        status_code=status,
        media_type=PROBLEM_MEDIA_TYPE,
    )


async def _http_exception(request: Request, exc: Exception) -> JSONResponse:
    assert isinstance(exc, StarletteHTTPException)
    code = {404: "not-found", 405: "method-not-allowed"}.get(
        exc.status_code, "http-error"
    )
    return problem_response(
        request,
        status=exc.status_code,
        code=code,
        title=str(exc.detail),
        detail=str(exc.detail),
    )


async def _validation_error(request: Request, exc: Exception) -> JSONResponse:
    assert isinstance(exc, RequestValidationError)
    # Deliberately drop pydantic's `input` so submitted values (e.g. names) are never echoed.
    errors = [
        FieldError(field=".".join(str(p) for p in err["loc"]), message=err["msg"])
        for err in exc.errors()
    ]
    return problem_response(
        request,
        status=422,
        code="validation-error",
        title="Invalid request",
        detail="One or more fields are invalid.",
        errors=[e.model_dump() for e in errors],
    )


async def _domain_error(request: Request, exc: Exception) -> JSONResponse:
    assert isinstance(exc, DomainError)
    return problem_response(
        request,
        status=exc.status,
        code=exc.code,
        title=exc.title,
        detail=exc.detail,
        **exc.extra(),
    )


async def _unhandled(request: Request, exc: Exception) -> JSONResponse:
    logger.exception("unhandled error", exc_info=exc)
    return problem_response(
        request, status=500, code="internal-error", title="Internal server error"
    )


class UnhandledErrorMiddleware(BaseHTTPMiddleware):
    """Turns any uncaught exception into a generic 500 problem.

    Added inside RequestIdMiddleware, so the request id is still set and the response
    still gets its X-Request-ID header. (Starlette's own catch-all runs outermost, after
    the request id is gone.) The traceback goes to the logs, never to the client.
    """

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        try:
            return await call_next(request)
        except Exception as exc:
            return await _unhandled(request, exc)


def register_exception_handlers(app: FastAPI) -> None:
    app.add_exception_handler(StarletteHTTPException, _http_exception)
    app.add_exception_handler(RequestValidationError, _validation_error)
    app.add_exception_handler(DomainError, _domain_error)
    app.add_exception_handler(Exception, _unhandled)
