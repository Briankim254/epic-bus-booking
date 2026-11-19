import logging
import uuid
from collections.abc import Callable
from datetime import datetime

from sqlalchemy.orm import Session

from app.core.clock import utcnow
from app.domain.errors import (
    BusInactive,
    BusNotFound,
    BusTooSmall,
    StaleStatus,
    TripNotFound,
    TripNotReassignable,
)
from app.domain.trip_status import REASSIGNABLE, TripStatus, assert_transition
from app.repositories.buses import BusRepository
from app.repositories.history import HistoryRepository
from app.repositories.trips import TripFilters, TripRepository
from app.schemas.trip import TripOut, TripPage, TripQuery

logger = logging.getLogger("app.trips")


class TripService:
    def __init__(
        self, session: Session, *, clock: Callable[[], datetime] = utcnow
    ) -> None:
        self._s = session
        self._clock = clock
        self._trips = TripRepository(session)
        self._buses = BusRepository(session)
        self._history = HistoryRepository(session)

    def search(self, query: TripQuery, *, bookable_only: bool) -> TripPage:
        rows, total = self._trips.search(
            TripFilters(query.origin_town_id, query.destination_town_id, query.date),
            sort=query.sort,
            limit=query.limit,
            offset=query.offset,
            bookable_at=self._clock() if bookable_only else None,
        )
        return TripPage(
            items=[TripOut.from_row(r) for r in rows],
            total=total,
            limit=query.limit,
            offset=query.offset,
        )

    def get(self, trip_id: uuid.UUID) -> TripOut:
        row = self._trips.get_row(trip_id)
        if row is None:
            raise TripNotFound
        return TripOut.from_row(row)

    def transition(self, trip_id: uuid.UUID, target: TripStatus) -> TripOut:
        try:
            trip = self._trips.get(trip_id)
            if trip is None:
                raise TripNotFound
            current = trip.status
            assert_transition(current, target)
            if not self._trips.set_status(trip_id, current, target):
                raise StaleStatus
            self._history.record(trip_id, current, target)
        except BaseException:
            self._s.rollback()
            raise
        self._s.commit()
        logger.info(
            "trip.transitioned",
            extra={"trip_id": str(trip_id), "from": current, "to": target},
        )
        return self.get(trip_id)

    def assign_bus(self, trip_id: uuid.UUID, bus_id: int) -> TripOut:
        try:
            bus = self._buses.get(bus_id)
            if bus is None:
                raise BusNotFound
            if not bus.active:
                raise BusInactive
            if not self._trips.assign_bus(trip_id, bus.id, bus.capacity):
                trip = self._trips.get(trip_id)
                if trip is None:
                    raise TripNotFound
                if trip.status not in REASSIGNABLE:
                    raise TripNotReassignable
                raise BusTooSmall(bus.capacity, trip.seats_booked)
        except BaseException:
            self._s.rollback()
            raise
        self._s.commit()
        logger.info("bus.assigned", extra={"trip_id": str(trip_id), "bus_id": bus_id})
        return self.get(trip_id)
