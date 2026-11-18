"""JSON logs with a per-request id. Never log passenger names or request bodies."""

import logging
import time
import uuid
from contextvars import ContextVar

from pythonjsonlogger.json import JsonFormatter
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

REQUEST_ID_HEADER = "X-Request-ID"
request_id_var: ContextVar[str | None] = ContextVar("request_id", default=None)

access_log = logging.getLogger("app.access")


class _RequestIdFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        if getattr(record, "request_id", None) is None:
            record.request_id = request_id_var.get()
        return True


def configure_logging(level: int = logging.INFO) -> None:
    handler = logging.StreamHandler()
    handler.setFormatter(
        JsonFormatter(
            "%(asctime)s %(levelname)s %(name)s %(message)s %(request_id)s",
            rename_fields={"asctime": "ts", "levelname": "level", "name": "logger"},
        )
    )
    handler.addFilter(_RequestIdFilter())
    root = logging.getLogger("app")
    root.handlers[:] = [handler]
    root.setLevel(level)
    root.propagate = False


class RequestIdMiddleware(BaseHTTPMiddleware):
    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        incoming = request.headers.get(REQUEST_ID_HEADER, "")
        request_id = incoming if 0 < len(incoming) <= 64 else uuid.uuid4().hex
        token = request_id_var.set(request_id)
        start = time.perf_counter()
        status = 500
        try:
            response = await call_next(request)
            status = response.status_code
            response.headers[REQUEST_ID_HEADER] = request_id
            return response
        finally:
            access_log.info(
                "request",
                extra={
                    "method": request.method,
                    "route": _route_template(request),
                    "status": status,
                    "duration_ms": round((time.perf_counter() - start) * 1000, 1),
                },
            )
            request_id_var.reset(token)


def _route_template(request: Request) -> str:
    """The path with matched parameters put back as {name}, so ids never reach the logs."""
    path = request.url.path
    for name, value in request.path_params.items():
        path = path.replace(str(value), "{" + name + "}")
    return path
