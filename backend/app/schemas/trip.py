import datetime as dt
import uuid

from pydantic import BaseModel, Field

from app.domain.trip_status import TripStatus
from app.repositories.trips import TripRow, TripSort
from app.schemas.bus import BusRef
from app.schemas.common import Currency, ORMModel
from app.schemas.town import TownOut


class TripOut(ORMModel):
    id: uuid.UUID
    origin: TownOut
    destination: TownOut
    bus: BusRef
    departs_at: dt.datetime = Field(description="UTC, ISO 8601")
    status: TripStatus
    capacity: int
    seats_booked: int
    seats_available: int
    fare_cents: int = Field(description="Per seat, US cents")
    currency: Currency = "USD"

    @classmethod
    def from_row(cls, row: TripRow) -> TripOut:
        t = row.trip
        return cls(
            id=t.id,
            origin=TownOut.model_validate(t.origin),
            destination=TownOut.model_validate(t.destination),
            bus=BusRef.model_validate(t.bus),
            departs_at=t.departs_at,
            status=t.status,
            capacity=t.capacity,
            seats_booked=t.seats_booked,
            seats_available=t.capacity - t.seats_booked,
            fare_cents=row.fare_cents,
        )


class TripPage(BaseModel):
    items: list[TripOut]
    total: int
    limit: int
    offset: int


class TripQuery(BaseModel):
    """Search parameters. `sort` is a whitelist; anything else is a 422."""

    origin_town_id: int | None = Field(default=None, ge=1)
    destination_town_id: int | None = Field(default=None, ge=1)
    date: dt.date | None = Field(
        default=None, description="Calendar day in Africa/Lagos (YYYY-MM-DD)"
    )
    sort: TripSort = "departs_at"
    limit: int = Field(default=20, ge=1, le=100)
    offset: int = Field(default=0, ge=0)


class TransitionIn(BaseModel):
    to_status: TripStatus


class BusAssignIn(BaseModel):
    bus_id: int = Field(ge=1)
