import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain.trip_status import TripStatus
from app.models import TripStatusHistory


class HistoryRepository:
    def __init__(self, session: Session) -> None:
        self._s = session

    def record(self, trip_id: uuid.UUID, from_: TripStatus, to: TripStatus) -> None:
        self._s.add(TripStatusHistory(trip_id=trip_id, from_status=from_, to_status=to))
        self._s.flush()

    def for_trip(self, trip_id: uuid.UUID) -> list[TripStatusHistory]:
        return list(
            self._s.scalars(
                select(TripStatusHistory)
                .where(TripStatusHistory.trip_id == trip_id)
                .order_by(TripStatusHistory.id)
            )
        )
