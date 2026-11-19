from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models import Booking

_REFERENCE_CONSTRAINT = "uq_bookings_reference"


def _constraint_name(exc: IntegrityError) -> str | None:
    diag = getattr(exc.orig, "diag", None)
    return getattr(diag, "constraint_name", None)


class BookingRepository:
    def __init__(self, session: Session) -> None:
        self._s = session

    def insert(self, booking: Booking) -> bool:
        """Insert inside a savepoint. False if the reference is already taken, so the
        caller can retry with a new one without losing the rest of the transaction."""
        try:
            with self._s.begin_nested():
                self._s.add(booking)
        except IntegrityError as exc:
            if _constraint_name(exc) == _REFERENCE_CONSTRAINT:
                return False
            raise
        return True

    def get_by_reference(self, reference: str) -> Booking | None:
        return self._s.scalar(select(Booking).where(Booking.reference == reference))
