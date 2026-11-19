import pytest
from app.services.bus_service import BusService
from sqlalchemy.orm import Session

from app.domain.errors import BusNotFound, DuplicatePlate
from app.schemas.bus import BusIn, BusPatch


def test_create_and_list(db: Session) -> None:
    created = BusService(db).create(BusIn(plate_number="lag-123-xy", capacity=18))
    assert created.plate_number == "LAG-123-XY"  # normalised
    assert created.active
    plates = [b.plate_number for b in BusService(db).list()]
    assert "LAG-123-XY" in plates and "TEST-001" in plates


def test_duplicate_plate(db: Session) -> None:
    with pytest.raises(DuplicatePlate):
        BusService(db).create(BusIn(plate_number="TEST-001", capacity=44))


def test_patch_changes_only_what_was_sent(db: Session) -> None:
    service = BusService(db)
    bus = service.create(BusIn(plate_number="NEW-1", name="Coach 9", capacity=30))
    updated = service.update(bus.id, BusPatch(active=False))
    assert (updated.name, updated.capacity, updated.active) == ("Coach 9", 30, False)


def test_patch_unknown_bus(db: Session) -> None:
    with pytest.raises(BusNotFound):
        BusService(db).update(999_999, BusPatch(capacity=10))
