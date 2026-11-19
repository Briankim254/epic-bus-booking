from datetime import timedelta

import pytest
from sqlalchemy import func, select, update
from sqlalchemy.orm import Session, sessionmaker

from app import cli
from app.models import IdempotencyKey
from app.schemas.booking import BookingIn
from app.services.booking_service import BookingService
from tests.factories import make_trip


def test_purge_idempotency_deletes_only_expired_keys(
    db: Session,
    session_factory: sessionmaker[Session],
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    trip = make_trip(db)
    service = BookingService(db)
    for key in ("old", "new"):
        service.create(
            BookingIn(trip_id=trip.id, passenger_name="Bola", seats=1),
            idempotency_key=key,
        )
    db.execute(
        update(IdempotencyKey)
        .where(IdempotencyKey.key == "old")
        .values(created_at=func.now() - timedelta(hours=25))
    )
    db.commit()

    monkeypatch.setattr(cli, "SessionLocal", session_factory)
    assert cli.main(["purge-idempotency"]) == 0
    assert "deleted 1" in capsys.readouterr().out
    assert list(db.scalars(select(IdempotencyKey.key))) == ["new"]
