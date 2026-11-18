from fastapi import FastAPI
from fastapi.routing import APIRoute
from starlette.middleware.cors import CORSMiddleware

from app.api.main import api_router
from app.core.config import settings
from app.core.errors import register_exception_handlers
from app.core.logging import REQUEST_ID_HEADER, RequestIdMiddleware, configure_logging


def custom_generate_unique_id(route: APIRoute) -> str:
    # `{tag}-{route_name}`: the generated client strips the tag prefix for method names
    return f"{route.tags[0]}-{route.name}"


def create_app() -> FastAPI:
    configure_logging()
    app = FastAPI(
        title=settings.PROJECT_NAME,
        openapi_url=f"{settings.API_V1_STR}/openapi.json",
        generate_unique_id_function=custom_generate_unique_id,
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.all_cors_origins,
        allow_credentials=False,
        allow_methods=["GET", "POST"],
        allow_headers=["Content-Type", "Idempotency-Key", REQUEST_ID_HEADER],
        expose_headers=[REQUEST_ID_HEADER, "Idempotent-Replayed"],
    )
    app.add_middleware(RequestIdMiddleware)
    register_exception_handlers(app)
    app.include_router(api_router, prefix=settings.API_V1_STR)
    return app


app = create_app()
