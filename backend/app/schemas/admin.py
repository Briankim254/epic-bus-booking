import uuid
from datetime import datetime

from pydantic import BaseModel


class DriftItem(BaseModel):
    trip_id: uuid.UUID
    counter: int
    actual: int


class DriftReport(BaseModel):
    checked_at: datetime
    drifted: list[DriftItem]
