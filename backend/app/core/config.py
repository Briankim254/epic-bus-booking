import json
import warnings
from typing import Annotated, Literal, Self

from pydantic import BeforeValidator, PostgresDsn, field_validator, model_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict


def _parse_list(value: str | list[str]) -> list[str]:
    if isinstance(value, str) and not value.startswith("["):
        return [item.strip() for item in value.split(",") if item.strip()]
    if isinstance(value, str):
        parsed: list[str] = json.loads(value)
        return parsed
    return value


def _use_psycopg_driver(value: str | PostgresDsn) -> str:
    url = str(value)
    for scheme in ("postgres://", "postgresql://"):
        if url.startswith(scheme):
            return url.replace(scheme, "postgresql+psycopg://", 1)
    return url


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        # Top-level .env, one level above ./backend/
        env_file="../.env",
        env_ignore_empty=True,
        extra="ignore",
    )

    PROJECT_NAME: str = "EPIC Booking"
    ENVIRONMENT: Literal["local", "test", "production"] = "local"
    API_V1_STR: str = "/api/v1"

    DATABASE_URL: PostgresDsn
    TEST_DATABASE_URL: PostgresDsn | None = None

    FRONTEND_HOST: str = "http://localhost:5173"
    BACKEND_CORS_ORIGINS: Annotated[
        list[str], NoDecode, BeforeValidator(_parse_list)
    ] = []

    @field_validator("DATABASE_URL", "TEST_DATABASE_URL", mode="before")
    @classmethod
    def _driver(cls, value: str | PostgresDsn | None) -> str | None:
        return None if value is None else _use_psycopg_driver(value)

    @property
    def all_cors_origins(self) -> list[str]:
        origins = [o.rstrip("/") for o in self.BACKEND_CORS_ORIGINS]
        return sorted({*origins, self.FRONTEND_HOST.rstrip("/")})

    def _check_default_secret(self, var_name: str, value: str | None) -> None:
        if value == "changethis":
            message = (
                f'The value of {var_name} is "changethis"; '
                "change it for anything other than local development."
            )
            if self.ENVIRONMENT == "production":
                raise ValueError(message)
            warnings.warn(message, stacklevel=1)

    @model_validator(mode="after")
    def _enforce_non_default_secrets(self) -> Self:
        for host in self.DATABASE_URL.hosts():
            self._check_default_secret("DATABASE_URL password", host["password"])
        return self


settings = Settings()
