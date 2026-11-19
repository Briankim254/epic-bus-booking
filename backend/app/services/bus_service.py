import logging

from sqlalchemy.orm import Session

from app.domain.errors import BusNotFound, DuplicatePlate
from app.models import Bus
from app.repositories.buses import BusRepository
from app.schemas.bus import BusIn, BusOut, BusPatch

logger = logging.getLogger("app.buses")


class BusService:
    """Bus edits never touch existing trips: a trip copied its bus's capacity when the
    bus was assigned (A9)."""

    def __init__(self, session: Session) -> None:
        self._s = session
        self._buses = BusRepository(session)

    def list(self) -> list[BusOut]:
        return [BusOut.model_validate(b) for b in self._buses.list()]

    def create(self, data: BusIn) -> BusOut:
        bus = Bus(
            plate_number=data.plate_number, name=data.name, capacity=data.capacity
        )
        if not self._buses.insert(bus):
            self._s.rollback()
            raise DuplicatePlate
        self._s.commit()
        logger.info("bus.created", extra={"bus_id": bus.id})
        return BusOut.model_validate(bus)

    def update(self, bus_id: int, patch: BusPatch) -> BusOut:
        bus = self._buses.get(bus_id)
        if bus is None:
            raise BusNotFound
        for field, value in patch.model_dump(exclude_unset=True).items():
            setattr(bus, field, value)
        self._s.commit()
        self._s.refresh(bus)
        logger.info("bus.updated", extra={"bus_id": bus.id})
        return BusOut.model_validate(bus)
