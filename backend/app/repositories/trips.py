"""All SQL for trips. `reserve_seats` is the only code path that changes seats_booked."""

import datetime as dt
import uuid
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Literal

from sqlalchemy import ColumnElement, Select, UnaryExpression, func, select, update
from sqlalchemy.orm import Session, aliased, joinedload

from app.domain.lagos_time import lagos_day_bounds
from app.domain.trip_status import BOOKABLE, REASSIGNABLE, TripStatus
from app.models import Booking, Town, Trip, ZoneFare

TripSort = Literal["departs_at", "-departs_at", "price", "-price"]


@dataclass(frozen=True)
class TripFilters:
    origin_town_id: int | None = None
    destination_town_id: int | None = None
    date: dt.date | None = None


@dataclass(frozen=True)
class TripRow:
    trip: Trip
    fare_cents: int


@dataclass(frozen=True)
class Drift:
    trip_id: uuid.UUID
    counter: int
    actual: int


_Origin = aliased(Town)
_Destination = aliased(Town)
# The fare joins on the unordered zone pair, so it is symmetric by construction.
_FARE_JOIN = (
    ZoneFare.zone_a_id == func.least(_Origin.zone_id, _Destination.zone_id)
) & (ZoneFare.zone_b_id == func.greatest(_Origin.zone_id, _Destination.zone_id))

# Whitelisted sorts: user input selects a key, never a column or SQL fragment.
_SORTS: dict[str, tuple[UnaryExpression[Any], ...]] = {
    "departs_at": (Trip.departs_at.asc(), Trip.id.asc()),
    "-departs_at": (Trip.departs_at.desc(), Trip.id.asc()),
    "price": (ZoneFare.fare_cents.asc(), Trip.departs_at.asc(), Trip.id.asc()),
    "-price": (ZoneFare.fare_cents.desc(), Trip.departs_at.asc(), Trip.id.asc()),
}


def _with_fare() -> Select[Trip, int]:
    return (
        select(Trip, ZoneFare.fare_cents)
        .join(_Origin, _Origin.id == Trip.origin_town_id)
        .join(_Destination, _Destination.id == Trip.destination_town_id)
        .join(ZoneFare, _FARE_JOIN)
        .options(
            joinedload(Trip.origin), joinedload(Trip.destination), joinedload(Trip.bus)
        )
    )


class TripRepository:
    def __init__(self, session: Session) -> None:
        self._s = session

    def search(
        self,
        filters: TripFilters,
        *,
        sort: TripSort,
        limit: int,
        offset: int,
        bookable_at: datetime | None,
    ) -> tuple[list[TripRow], int]:
        """`bookable_at` set: only trips a customer could book at that moment."""
        where: list[ColumnElement[bool]] = []
        if filters.origin_town_id is not None:
            where.append(Trip.origin_town_id == filters.origin_town_id)
        if filters.destination_town_id is not None:
            where.append(Trip.destination_town_id == filters.destination_town_id)
        if filters.date is not None:
            start, end = lagos_day_bounds(filters.date)
            where += [Trip.departs_at >= start, Trip.departs_at < end]
        if bookable_at is not None:
            where += [
                Trip.status.in_(BOOKABLE),
                Trip.departs_at > bookable_at,
                Trip.seats_booked < Trip.capacity,
            ]
        total = self._s.scalar(select(func.count()).select_from(Trip).where(*where))
        rows = self._s.execute(
            _with_fare()
            .where(*where)
            .order_by(*_SORTS[sort])
            .limit(limit)
            .offset(offset)
        ).all()
        return [TripRow(trip, fare) for trip, fare in rows], total or 0

    def get(self, trip_id: uuid.UUID) -> Trip | None:
        return self._s.get(Trip, trip_id, populate_existing=True)

    def get_row(self, trip_id: uuid.UUID) -> TripRow | None:
        row = self._s.execute(
            _with_fare()
            .where(Trip.id == trip_id)
            .execution_options(populate_existing=True)
        ).first()
        return TripRow(row[0], row[1]) if row else None

    def reserve_seats(self, trip_id: uuid.UUID, seats: int, now: datetime) -> bool:
        """Layer 1 of overbooking protection: check and write in one statement.

        Concurrent callers queue on the row lock; each re-checks the WHERE against the
        committed row, so the last seat goes to exactly one of them. The CHECK
        ck_trips_seats_range is layer 2.
        """
        stmt = (
            update(Trip)
            .where(
                Trip.id == trip_id,
                Trip.status.in_(BOOKABLE),
                Trip.departs_at > now,
                Trip.seats_booked + seats <= Trip.capacity,
            )
            .values(seats_booked=Trip.seats_booked + seats, updated_at=func.now())
            .returning(Trip.id)
            .execution_options(synchronize_session=False)
        )
        return self._s.execute(stmt).first() is not None

    def set_status(
        self, trip_id: uuid.UUID, current: TripStatus, target: TripStatus
    ) -> bool:
        """Conditional on the status the caller read, so two operators can't skip a step."""
        stmt = (
            update(Trip)
            .where(Trip.id == trip_id, Trip.status == current)
            .values(status=target, updated_at=func.now())
            .returning(Trip.id)
            .execution_options(synchronize_session=False)
        )
        return self._s.execute(stmt).first() is not None

    def assign_bus(self, trip_id: uuid.UUID, bus_id: int, capacity: int) -> bool:
        """Move a trip to another bus, copying its capacity (A9, A10). One statement, so
        it can't race a booking into breaking seats_booked <= capacity."""
        stmt = (
            update(Trip)
            .where(
                Trip.id == trip_id,
                Trip.status.in_(REASSIGNABLE),
                Trip.seats_booked <= capacity,
            )
            .values(bus_id=bus_id, capacity=capacity, updated_at=func.now())
            .returning(Trip.id)
            .execution_options(synchronize_session=False)
        )
        return self._s.execute(stmt).first() is not None

    def find_drift(self) -> list[Drift]:
        actual = func.coalesce(func.sum(Booking.seats), 0)
        rows = self._s.execute(
            select(Trip.id, Trip.seats_booked, actual)
            .outerjoin(Booking, Booking.trip_id == Trip.id)
            .group_by(Trip.id)
            .having(Trip.seats_booked != actual)
        ).all()
        return [Drift(trip_id=r[0], counter=r[1], actual=r[2]) for r in rows]
