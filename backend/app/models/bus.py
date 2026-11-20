from sqlalchemy import CheckConstraint, String, true
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base
from app.models.mixins import TimestampMixin


class Bus(TimestampMixin, Base):
    """A vehicle in the fleet. A trip copies the bus's capacity when the bus is assigned"""

    __tablename__ = "buses"
    __table_args__ = (CheckConstraint("capacity > 0", name="capacity_pos"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    plate_number: Mapped[str] = mapped_column(String(20), unique=True)
    name: Mapped[str | None] = mapped_column(String(50))
    capacity: Mapped[int]
    active: Mapped[bool] = mapped_column(server_default=true(), default=True)
