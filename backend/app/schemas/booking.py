import unicodedata
import uuid
from datetime import datetime
from typing import Annotated

from pydantic import AfterValidator, BaseModel, Field

from app.domain.booking_rules import MAX_SEATS_PER_BOOKING
from app.schemas.trip import TripOut

NAME_MAX = 100


def _clean_name(value: str) -> str:
    """NFC-normalise and trim. Unicode letters (Ọláyíwọlá, Ngọzi) are welcome; control
    and format characters are not. Messages never repeat the submitted value."""
    value = unicodedata.normalize("NFC", value).strip()
    if not value:
        raise ValueError("must not be blank")
    if len(value) > NAME_MAX:
        raise ValueError(f"must be at most {NAME_MAX} characters")
    if any(unicodedata.category(ch).startswith("C") for ch in value):
        raise ValueError("must not contain control characters")
    return value


PassengerName = Annotated[
    str, Field(min_length=1, max_length=NAME_MAX), AfterValidator(_clean_name)
]


class BookingIn(BaseModel):
    trip_id: uuid.UUID
    passenger_name: PassengerName
    seats: int = Field(ge=1, le=MAX_SEATS_PER_BOOKING)


class BookingOut(BaseModel):
    reference: str
    trip: TripOut
    passenger_name: str
    seats: int
    fare_cents_per_seat: int
    total_cents: int
    created_at: datetime
