"""Booking service against a real Postgres (PLAN §7.4)."""

import uuid
from collections.abc import Callable, Iterator
from datetime import UTC, datetime, timedelta

import pytest
from app.services.booking_service import BookingService
from sqlalchemy import func, select, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.domain.errors import (
    IdempotencyKeyReused,
    InsufficientSeats,
    TripNotBookable,
    TripNotFound,
)
from app.domain.trip_status import TripStatus
from app.models import Booking, Trip
from app.schemas.booking import BookingIn
from app.services.reconciliation import find_drift
from tests.factories import make_trip


def _req(trip: Trip, seats: int = 1, name: str = "Adaeze Okoro") -> BookingIn:
    return BookingIn(trip_id=trip.id, passenger_name=name, seats=seats)


def test_booking_takes_seats_and_snapshots_the_fare(db: Session) -> None:
    trip = make_trip(db, origin="Lagos", destination="Abuja")  # zones 1 -> 3: $25
    result = BookingService(db).create(_req(trip, seats=3))

    assert not result.replayed
    b = result.booking
    assert b.reference.startswith("BK-")
    assert (b.seats, b.fare_cents_per_seat, b.total_cents) == (3, 2500, 7500)
    assert b.trip.seats_booked == 3
    assert b.trip.seats_available == trip.capacity - 3
    db.refresh(trip)
    assert trip.seats_booked == 3


def test_exact_remaining_seats_succeeds(db: Session) -> None:
    trip = make_trip(db, capacity=44, seats_booked=40)
    BookingService(db).create(_req(trip, seats=4))
    db.refresh(trip)
    assert trip.seats_booked == 44


def test_one_more_than_remaining_fails_and_reports_remaining(db: Session) -> None:
    trip = make_trip(db, capacity=44, seats_booked=40)
    with pytest.raises(InsufficientSeats) as exc:
        BookingService(db).create(_req(trip, seats=5))
    assert exc.value.remaining == 4
    db.refresh(trip)
    assert trip.seats_booked == 40
    assert db.scalar(select(func.count()).select_from(Booking)) == 0


@pytest.mark.parametrize(
    "status", [s for s in TripStatus if s is not TripStatus.SCHEDULED]
)
def test_non_scheduled_trips_are_not_bookable(db: Session, status: TripStatus) -> None:
    trip = make_trip(db, status=status)
    with pytest.raises(TripNotBookable):
        BookingService(db).create(_req(trip))


def test_departed_by_the_clock_is_not_bookable(db: Session) -> None:
    trip = make_trip(db, departs_in=timedelta(hours=1))
    later = datetime.now(UTC) + timedelta(hours=2)
    with pytest.raises(TripNotBookable):
        BookingService(db, clock=lambda: later).create(_req(trip))


def test_unknown_trip(db: Session) -> None:
    with pytest.raises(TripNotFound):
        BookingService(db).create(
            BookingIn(trip_id=uuid.uuid4(), passenger_name="Bola", seats=1)
        )


def _references(*values: str) -> Callable[[], str]:
    it: Iterator[str] = iter(values)
    return lambda: next(it)


def test_reference_collision_is_retried(db: Session) -> None:
    trip = make_trip(db)
    BookingService(db, new_reference=_references("BK-AAAA-AAAA")).create(_req(trip))
    second = BookingService(
        db, new_reference=_references("BK-AAAA-AAAA", "BK-BBBB-BBBB")
    ).create(_req(trip))
    assert second.booking.reference == "BK-BBBB-BBBB"
    db.refresh(trip)
    assert trip.seats_booked == 2
    assert find_drift(db) == []


def test_lookup_by_reference(db: Session) -> None:
    trip = make_trip(db)
    made = BookingService(db).create(_req(trip, name="Ngọzi Ádá")).booking
    found = BookingService(db).get(made.reference)
    assert found.passenger_name == "Ngọzi Ádá"
    assert found.total_cents == made.total_cents


class TestIdempotency:
    def test_replay_returns_the_same_booking_and_moves_the_counter_once(
        self, db: Session
    ) -> None:
        trip = make_trip(db)
        first = BookingService(db).create(_req(trip, seats=2), idempotency_key="k-1")
        again = BookingService(db).create(_req(trip, seats=2), idempotency_key="k-1")

        assert again.replayed and not first.replayed
        assert again.booking == first.booking
        db.refresh(trip)
        assert trip.seats_booked == 2
        assert db.scalar(select(func.count()).select_from(Booking)) == 1

    def test_same_key_different_body_is_rejected(self, db: Session) -> None:
        trip = make_trip(db)
        BookingService(db).create(_req(trip, seats=2), idempotency_key="k-2")
        with pytest.raises(IdempotencyKeyReused):
            BookingService(db).create(_req(trip, seats=3), idempotency_key="k-2")

    def test_key_from_a_failed_attempt_can_be_retried(self, db: Session) -> None:
        trip = make_trip(db, capacity=44, seats_booked=43)
        with pytest.raises(InsufficientSeats):
            BookingService(db).create(_req(trip, seats=2), idempotency_key="k-3")
        # Nothing was stored for the failure, so the same key works for a valid request.
        ok = BookingService(db).create(_req(trip, seats=1), idempotency_key="k-3")
        assert not ok.replayed


def test_check_constraint_blocks_overbooking_on_its_own(db: Session) -> None:
    """Layer 2: even a raw UPDATE that bypasses the service cannot overbook."""
    trip = make_trip(db)
    with pytest.raises(IntegrityError, match="ck_trips_seats_range"):
        db.execute(
            text("UPDATE trips SET seats_booked = capacity + 1 WHERE id = :id"),
            {"id": trip.id},
        )
    db.rollback()
