"""updated_at moves on every write path without the caller setting it (models/mixins.py).

Each write runs in its own transaction after the setup commit, and now() is the
transaction's start time, so the new value is strictly later.
"""

from datetime import UTC, datetime

from sqlalchemy.orm import Session

from app.domain.trip_status import TripStatus
from app.repositories.trips import TripRepository
from app.schemas.bus import BusPatch
from app.services.bus_service import BusService
from app.services.trip_service import TripService
from tests.factories import bus, make_trip


def test_reserve_seats_bumps_updated_at(db: Session) -> None:
    trip = make_trip(db)
    before = trip.updated_at
    assert TripRepository(db).reserve_seats(trip.id, 1, datetime.now(UTC))
    db.commit()
    db.refresh(trip)
    assert trip.updated_at > before


def test_status_transition_bumps_updated_at(db: Session) -> None:
    trip = make_trip(db)
    before = trip.updated_at
    TripService(db).transition(trip.id, TripStatus.BOARDING)
    db.refresh(trip)
    assert trip.updated_at > before


def test_bus_reassignment_bumps_updated_at(db: Session) -> None:
    trip = make_trip(db, bus_plate="TEST-001")
    before = trip.updated_at
    TripService(db).assign_bus(trip.id, bus(db, "TEST-002").id)
    db.refresh(trip)
    assert trip.updated_at > before


def test_bus_edit_bumps_updated_at(db: Session) -> None:
    target = bus(db, "TEST-003")
    before = target.updated_at
    created = target.created_at
    BusService(db).update(target.id, BusPatch(name="Renamed"))
    db.refresh(target)
    assert target.updated_at > before
    assert target.created_at == created
