from typing import Annotated

from pydantic import BaseModel, Field, StringConstraints

from app.schemas.common import ORMModel

Plate = Annotated[
    str,
    StringConstraints(
        strip_whitespace=True, to_upper=True, min_length=1, max_length=20
    ),
]
BusName = Annotated[str, StringConstraints(strip_whitespace=True, max_length=50)]
Capacity = Annotated[int, Field(ge=1, le=100)]


class BusRef(ORMModel):
    id: int
    plate_number: str
    name: str | None


class BusOut(BusRef):
    capacity: int
    active: bool


class BusIn(BaseModel):
    plate_number: Plate
    name: BusName | None = None
    capacity: Capacity


class BusPatch(BaseModel):
    """Only the fields sent are changed. The plate number is the bus's identity: fixed."""

    name: BusName | None = None
    capacity: Capacity | None = None
    active: bool | None = None
