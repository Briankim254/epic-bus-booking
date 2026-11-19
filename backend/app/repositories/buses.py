from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models import Bus

_PLATE_CONSTRAINT = "uq_buses_plate_number"


class BusRepository:
    def __init__(self, session: Session) -> None:
        self._s = session

    def list(self) -> list[Bus]:
        return list(self._s.scalars(select(Bus).order_by(Bus.plate_number)))

    def get(self, bus_id: int) -> Bus | None:
        return self._s.get(Bus, bus_id, populate_existing=True)

    def insert(self, bus: Bus) -> bool:
        """False if the plate number is taken (the UNIQUE constraint decides, not a read)."""
        try:
            with self._s.begin_nested():
                self._s.add(bus)
        except IntegrityError as exc:
            diag = getattr(exc.orig, "diag", None)
            if getattr(diag, "constraint_name", None) == _PLATE_CONSTRAINT:
                return False
            raise
        return True
