"""seats_booked is a denormalised counter; this checks it against the bookings table."""

import uuid
from dataclasses import dataclass

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import Booking, Trip


@dataclass(frozen=True)
class Drift:
    trip_id: uuid.UUID
    counter: int
    actual: int


def find_drift(session: Session) -> list[Drift]:
    actual = func.coalesce(func.sum(Booking.seats), 0)
    rows = session.execute(
        select(Trip.id, Trip.seats_booked, actual)
        .outerjoin(Booking, Booking.trip_id == Trip.id)
        .group_by(Trip.id)
        .having(Trip.seats_booked != actual)
    ).all()
    return [Drift(trip_id=r[0], counter=r[1], actual=r[2]) for r in rows]
