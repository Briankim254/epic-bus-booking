"""Plain factory functions for integration and API tests. No factory_boy."""

from datetime import UTC, datetime, timedelta

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.domain.trip_status import TripStatus
from app.models import Bus, Town, Trip


def town_id(session: Session, name: str) -> int:
    found = session.scalar(select(Town.id).where(Town.name == name))
    assert found is not None, f"unknown town {name}"
    return found


def bus(session: Session, plate: str = "TEST-001") -> Bus:
    found = session.scalar(select(Bus).where(Bus.plate_number == plate))
    assert found is not None, f"unknown bus {plate}"
    return found


def make_trip(
    session: Session,
    *,
    origin: str = "Lagos",
    destination: str = "Abuja",
    bus_plate: str = "TEST-001",
    capacity: int | None = None,
    seats_booked: int = 0,
    status: TripStatus = TripStatus.SCHEDULED,
    departs_at: datetime | None = None,
    departs_in: timedelta = timedelta(hours=2),
) -> Trip:
    """Insert and commit a trip. `capacity` defaults to the bus's (assumption A9).

    `seats_booked` and `status` are set directly: this is test setup, not a code path
    the application uses.
    """
    assigned = bus(session, bus_plate)
    trip = Trip(
        origin_town_id=town_id(session, origin),
        destination_town_id=town_id(session, destination),
        bus_id=assigned.id,
        capacity=capacity if capacity is not None else assigned.capacity,
        departs_at=departs_at or datetime.now(UTC) + departs_in,
        status=status,
    )
    session.add(trip)
    session.flush()
    if seats_booked:
        session.execute(
            update(Trip).where(Trip.id == trip.id).values(seats_booked=seats_booked)
        )
    session.commit()
    session.refresh(trip)
    return trip
