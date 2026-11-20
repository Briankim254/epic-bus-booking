import uuid

from sqlalchemy import CheckConstraint, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base
from app.models.mixins import CreatedAtMixin


class Booking(CreatedAtMixin, Base):
    """A row exists only for a confirmed booking. The fare is snapshotted at booking time."""

    __tablename__ = "bookings"
    __table_args__ = (
        CheckConstraint("seats > 0", name="seats_pos"),
        CheckConstraint(
            "total_cents = seats * fare_cents_per_seat", name="total_match"
        ),
        CheckConstraint("length(btrim(passenger_name)) > 0", name="name_present"),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    reference: Mapped[str] = mapped_column(String(12), unique=True)
    trip_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("trips.id"), index=True)
    passenger_name: Mapped[str] = mapped_column(String(100))
    seats: Mapped[int]
    fare_cents_per_seat: Mapped[int]
    total_cents: Mapped[int]
