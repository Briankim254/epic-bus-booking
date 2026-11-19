"""Races, with real threads and separate connections (PLAN §7.4).

Each thread gets its own session; a Barrier releases them together. Run these repeatedly:
  for i in $(seq 20); do uv run pytest tests/integration/test_concurrency.py -q || break; done
"""

import threading
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor

from sqlalchemy import func, select
from sqlalchemy.orm import Session, sessionmaker

from app.domain.errors import BusTooSmall, DomainError, InsufficientSeats
from app.models import Booking, Bus, Trip
from app.schemas.booking import BookingIn
from app.services.booking_service import BookingService
from app.services.reconciliation import find_drift
from app.services.trip_service import TripService
from tests.factories import make_trip


def _race[T](
    factory: sessionmaker[Session], n: int, work: Callable[[Session, int], T]
) -> list[T | Exception]:
    barrier = threading.Barrier(n)

    def run(i: int) -> T | Exception:
        with factory() as session:
            barrier.wait()
            try:
                return work(session, i)
            except DomainError as exc:
                return exc

    with ThreadPoolExecutor(max_workers=n) as pool:
        return list(pool.map(run, range(n)))


def test_twenty_customers_one_last_seat(
    db: Session, session_factory: sessionmaker[Session]
) -> None:
    trip = make_trip(db, capacity=1)

    def book(session: Session, i: int) -> object:
        return BookingService(session).create(
            BookingIn(trip_id=trip.id, passenger_name=f"Passenger {i}", seats=1)
        )

    results = _race(session_factory, 20, book)

    failures = [r for r in results if isinstance(r, Exception)]
    assert len(results) - len(failures) == 1
    assert len(failures) == 19
    assert all(isinstance(f, InsufficientSeats) for f in failures)
    db.refresh(trip)
    assert trip.seats_booked == 1
    assert find_drift(db) == []


def test_five_seats_twenty_customers(
    db: Session, session_factory: sessionmaker[Session]
) -> None:
    trip = make_trip(db, capacity=5)

    def book(session: Session, i: int) -> object:
        return BookingService(session).create(
            BookingIn(trip_id=trip.id, passenger_name=f"Passenger {i}", seats=1)
        )

    results = _race(session_factory, 20, book)
    assert sum(not isinstance(r, Exception) for r in results) == 5
    db.refresh(trip)
    assert trip.seats_booked == 5
    assert find_drift(db) == []


def test_same_idempotency_key_from_ten_threads_books_once(
    db: Session, session_factory: sessionmaker[Session]
) -> None:
    trip = make_trip(db)
    request = BookingIn(trip_id=trip.id, passenger_name="Double Clicker", seats=2)

    def book(session: Session, _: int) -> object:
        return BookingService(session).create(request, idempotency_key="same-key")

    results = _race(session_factory, 10, book)
    assert not any(isinstance(r, Exception) for r in results)
    assert db.scalar(select(func.count()).select_from(Booking)) == 1
    db.refresh(trip)
    assert trip.seats_booked == 2


def test_reassignment_racing_bookings_never_breaks_capacity(
    db: Session, session_factory: sessionmaker[Session]
) -> None:
    """A 44-seat trip with 38 booked moves to a 40-seat bus while 8 customers each book
    one seat. Whatever the interleaving, seats_booked <= capacity and nothing drifts."""
    trip = make_trip(db, bus_plate="TEST-001", seats_booked=0)
    for i in range(38):  # real bookings, so reconciliation has rows to compare
        BookingService(db).create(
            BookingIn(trip_id=trip.id, passenger_name=f"Early {i}", seats=1)
        )
    small = db.scalar(select(Bus).where(Bus.plate_number == "TEST-003"))
    assert small is not None and small.capacity == 40

    def act(session: Session, i: int) -> object:
        if i == 0:
            return TripService(session).assign_bus(trip.id, small.id)
        return BookingService(session).create(
            BookingIn(trip_id=trip.id, passenger_name=f"Late {i}", seats=1)
        )

    results = _race(session_factory, 9, act)
    assert all(
        isinstance(r, (InsufficientSeats, BusTooSmall)) or not isinstance(r, Exception)
        for r in results
    )
    fresh = db.get(Trip, trip.id, populate_existing=True)
    assert fresh is not None
    assert fresh.seats_booked <= fresh.capacity
    assert find_drift(db) == []
