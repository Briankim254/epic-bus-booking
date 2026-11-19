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
