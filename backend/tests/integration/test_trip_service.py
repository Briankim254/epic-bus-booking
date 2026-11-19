"""Trip transitions and bus reassignment (PLAN §7.5)."""

import uuid

import pytest
from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.domain.errors import (
    BusInactive,
    BusNotFound,
    BusTooSmall,
    StaleStatus,
    TripNotFound,
    TripNotReassignable,
)
from app.domain.trip_status import InvalidTransition, TripStatus
from app.models import Bus, Trip
from app.repositories.history import HistoryRepository
from app.repositories.trips import TripRepository
from app.schemas.bus import BusPatch
from app.services.bus_service import BusService
from app.services.trip_service import TripService
from tests.factories import bus, make_trip


def test_valid_transition_persists_and_writes_history(db: Session) -> None:
    trip = make_trip(db)
    out = TripService(db).transition(trip.id, TripStatus.BOARDING)
    assert out.status is TripStatus.BOARDING
    db.refresh(trip)
    assert trip.status is TripStatus.BOARDING
    [entry] = HistoryRepository(db).for_trip(trip.id)
    assert (entry.from_status, entry.to_status) == (
        TripStatus.SCHEDULED,
        TripStatus.BOARDING,
    )


def test_invalid_transition_is_rejected(db: Session) -> None:
    trip = make_trip(db)
    with pytest.raises(InvalidTransition):
        TripService(db).transition(trip.id, TripStatus.ARRIVED)
    assert HistoryRepository(db).for_trip(trip.id) == []


def test_unknown_trip(db: Session) -> None:
    with pytest.raises(TripNotFound):
        TripService(db).transition(uuid.uuid4(), TripStatus.BOARDING)


def test_stale_status_is_a_conflict(db: Session) -> None:
    """The conditional UPDATE matches 0 rows when someone else moved the trip first."""
    trip = make_trip(db)
    repo = TripRepository(db)
    assert repo.set_status(trip.id, TripStatus.SCHEDULED, TripStatus.BOARDING)
    db.commit()
    assert not repo.set_status(trip.id, TripStatus.SCHEDULED, TripStatus.BOARDING)
    db.rollback()


def test_stale_status_raised_by_service(
    db: Session, monkeypatch: pytest.MonkeyPatch
) -> None:
    trip = make_trip(db)
    monkeypatch.setattr(TripRepository, "set_status", lambda *a, **k: False)
    with pytest.raises(StaleStatus):
        TripService(db).transition(trip.id, TripStatus.BOARDING)


class TestReassignment:
    def test_moves_the_trip_and_copies_the_capacity(self, db: Session) -> None:
        trip = make_trip(db, bus_plate="TEST-001", seats_booked=10)
        target = bus(db, "TEST-003")
        out = TripService(db).assign_bus(trip.id, target.id)
        assert (out.bus.plate_number, out.capacity, out.seats_booked) == (
            "TEST-003",
            40,
            10,
        )

    def test_not_while_trip_is_past_scheduled(self, db: Session) -> None:
        trip = make_trip(db, status=TripStatus.BOARDING)
        with pytest.raises(TripNotReassignable):
            TripService(db).assign_bus(trip.id, bus(db, "TEST-003").id)

    def test_not_to_an_inactive_bus(self, db: Session) -> None:
        trip = make_trip(db)
        target = bus(db, "TEST-003")
        db.execute(update(Bus).where(Bus.id == target.id).values(active=False))
        db.commit()
        with pytest.raises(BusInactive):
            TripService(db).assign_bus(trip.id, target.id)

    def test_not_to_a_bus_smaller_than_the_bookings(self, db: Session) -> None:
        trip = make_trip(db, bus_plate="TEST-001", seats_booked=41)
        with pytest.raises(BusTooSmall) as exc:
            TripService(db).assign_bus(trip.id, bus(db, "TEST-003").id)
        assert exc.value.seats_booked == 41

    def test_unknown_bus_and_trip(self, db: Session) -> None:
        trip = make_trip(db)
        with pytest.raises(BusNotFound):
            TripService(db).assign_bus(trip.id, 999_999)
        with pytest.raises(TripNotFound):
            TripService(db).assign_bus(uuid.uuid4(), bus(db).id)

    def test_editing_a_bus_leaves_its_trips_alone(self, db: Session) -> None:
        trip = make_trip(db, bus_plate="TEST-001")
        BusService(db).update(bus(db, "TEST-001").id, BusPatch(capacity=50))
        db.refresh(trip)
        assert trip.capacity == 44


def test_new_trips_still_take_capacity_from_their_bus(db: Session) -> None:
    trip = make_trip(db, bus_plate="TEST-004")
    found = db.scalar(select(Trip.capacity).where(Trip.id == trip.id))
    assert found == 40
