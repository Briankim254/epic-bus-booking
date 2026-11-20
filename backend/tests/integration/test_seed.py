"""The seed runs end to end through the real services."""

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.domain.trip_status import TripStatus
from app.models import Booking, Trip, TripStatusHistory
from app.seed import BOOKINGS, TRIPS, seed
from app.services.reconciliation import find_drift


def test_seed_creates_the_demo_data_and_is_idempotent(db: Session) -> None:
    seed(db)
    seed(db)  # second run: no duplicates

    assert db.scalar(select(func.count()).select_from(Trip)) == len(TRIPS)
    assert db.scalar(select(func.count()).select_from(Booking)) == len(BOOKINGS)
    assert find_drift(db) == []
    statuses = set(db.scalars(select(Trip.status)))
    assert {TripStatus.SCHEDULED, TripStatus.DEPARTED, TripStatus.ARRIVED} <= statuses
    # departed = 2 steps, arrived = 4 steps, each recorded once
    assert db.scalar(select(func.count()).select_from(TripStatusHistory)) == 6


def test_seed_reset_rebuilds(db: Session) -> None:
    seed(db)
    seed(db, reset=True)
    assert db.scalar(select(func.count()).select_from(Booking)) == len(BOOKINGS)
    assert find_drift(db) == []


def test_seed_can_be_anchored_to_a_demo_day(db: Session) -> None:
    from datetime import date

    from app.domain.lagos_time import LAGOS
    from app.seed import anchored_now

    seed(db, now=anchored_now(date(2026, 11, 24)))
    by_status = {
        status: sorted(
            t.astimezone(LAGOS).date().isoformat()
            for t in db.scalars(select(Trip.departs_at).where(Trip.status == status))
        )
        for status in (TripStatus.DEPARTED, TripStatus.ARRIVED, TripStatus.SCHEDULED)
    }
    assert by_status[TripStatus.DEPARTED] == ["2026-11-24"]  # on the road that morning
    assert by_status[TripStatus.ARRIVED] == ["2026-11-23"]
    assert set(by_status[TripStatus.SCHEDULED]) == {
        "2026-11-25",
        "2026-11-26",
        "2026-11-27",
    }
    assert find_drift(db) == []
