from datetime import datetime
from typing import Any

from sqlalchemy import delete, select, update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from app.models import IdempotencyKey


class IdempotencyRepository:
    def __init__(self, session: Session) -> None:
        self._s = session

    def claim(self, scope: str, key: str, request_hash: str) -> bool:
        """True if this transaction now owns the key.

        A concurrent claim of the same key blocks on the primary key until the first
        transaction ends, then either sees its committed row (False) or, if it rolled
        back, claims the key itself (True). No "in progress" state is needed.
        """
        stmt = (
            insert(IdempotencyKey)
            .values(scope=scope, key=key, request_hash=request_hash)
            .on_conflict_do_nothing(index_elements=["scope", "key"])
            .returning(IdempotencyKey.key)
        )
        return self._s.execute(stmt).first() is not None

    def get(self, scope: str, key: str) -> IdempotencyKey | None:
        return self._s.scalar(
            select(IdempotencyKey)
            .where(IdempotencyKey.scope == scope, IdempotencyKey.key == key)
            .execution_options(populate_existing=True)
        )

    def store_response(
        self, scope: str, key: str, status: int, body: dict[str, Any]
    ) -> None:
        self._s.execute(
            update(IdempotencyKey)
            .where(IdempotencyKey.scope == scope, IdempotencyKey.key == key)
            .values(response_status=status, response_body=body)
            .execution_options(synchronize_session=False)
        )

    def purge(self, older_than: datetime) -> int:
        result = self._s.execute(
            delete(IdempotencyKey)
            .where(IdempotencyKey.created_at < older_than)
            .returning(IdempotencyKey.key)
            .execution_options(synchronize_session=False)
        )
        return len(result.all())
