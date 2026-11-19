"""Import every model module here, or Alembic autogenerate will not see its tables."""

from app.models.base import Base
from app.models.booking import Booking
from app.models.bus import Bus
from app.models.geography import Town, Zone, ZoneFare
from app.models.idempotency import IdempotencyKey
from app.models.trip import Trip
from app.models.trip_status_history import TripStatusHistory

__all__ = [
    "Base",
    "Booking",
    "Bus",
    "IdempotencyKey",
    "Town",
    "Trip",
    "TripStatusHistory",
    "Zone",
    "ZoneFare",
]
