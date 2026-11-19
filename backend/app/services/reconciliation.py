"""seats_booked is a denormalised counter; this checks it against the bookings table.

Never auto-repair: drift means a bug, so it is reported and alerted on.
"""

import logging
from collections.abc import Callable
from datetime import datetime

from sqlalchemy.orm import Session

from app.core.clock import utcnow
from app.repositories.trips import Drift, TripRepository
from app.schemas.admin import DriftItem, DriftReport

__all__ = ["Drift", "find_drift", "report"]

logger = logging.getLogger("app.reconciliation")


def find_drift(session: Session) -> list[Drift]:
    return TripRepository(session).find_drift()


def report(session: Session, *, clock: Callable[[], datetime] = utcnow) -> DriftReport:
    drift = find_drift(session)
    for d in drift:
        logger.error(
            "reconciliation.drift",
            extra={"trip_id": str(d.trip_id), "counter": d.counter, "actual": d.actual},
        )
    return DriftReport(
        checked_at=clock(),
        drifted=[
            DriftItem(trip_id=d.trip_id, counter=d.counter, actual=d.actual)
            for d in drift
        ],
    )
