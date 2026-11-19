from datetime import datetime
from typing import Any

from sqlalchemy import CHAR, DateTime, Index, SmallInteger, String, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class IdempotencyKey(Base):
    """One row per (operation, Idempotency-Key), written in the booking's own transaction.

    The row is claimed first (response columns empty) and filled in before commit, so a
    committed row always has a response. A failed booking rolls the claim back with it.
    """

    __tablename__ = "idempotency_keys"
    __table_args__ = (Index("ix_idempotency_keys_created_at", "created_at"),)

    scope: Mapped[str] = mapped_column(String(40), primary_key=True)
    key: Mapped[str] = mapped_column(String(255), primary_key=True)
    request_hash: Mapped[str] = mapped_column(CHAR(64))  # sha256 of the canonical body
    response_status: Mapped[int | None] = mapped_column(SmallInteger)
    response_body: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
