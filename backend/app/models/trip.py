import uuid
from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, Enum, ForeignKey, Index, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.domain.trip_status import TripStatus
from app.models.base import Base
from app.models.bus import Bus
from app.models.geography import Town

_STATUS_VALUES = ", ".join(f"'{s.value}'" for s in TripStatus)


class Trip(Base):
    __tablename__ = "trips"
    __table_args__ = (
        CheckConstraint("origin_town_id <> destination_town_id", name="distinct_towns"),
        CheckConstraint("capacity > 0", name="capacity_pos"),
        # The backstop: no code path, script or manual UPDATE can overbook.
        CheckConstraint(
            "seats_booked >= 0 AND seats_booked <= capacity", name="seats_range"
        ),
        CheckConstraint(f"status IN ({_STATUS_VALUES})", name="status_valid"),
        Index(
            "ix_trips_route_departs_at",
            "origin_town_id",
            "destination_town_id",
            "departs_at",
        ),
        Index("ix_trips_status_departs_at", "status", "departs_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    origin_town_id: Mapped[int] = mapped_column(ForeignKey("towns.id"))
    destination_town_id: Mapped[int] = mapped_column(ForeignKey("towns.id"))
    bus_id: Mapped[int] = mapped_column(ForeignKey("buses.id"), index=True)
    departs_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    capacity: Mapped[int]  # copied from the bus when it is assigned (A9)
    seats_booked: Mapped[int] = mapped_column(server_default="0", default=0)
    status: Mapped[TripStatus] = mapped_column(
        Enum(
            TripStatus,
            native_enum=False,
            length=20,
            create_constraint=False,
            values_callable=lambda e: [m.value for m in e],
        ),
        server_default=TripStatus.SCHEDULED.value,
        default=TripStatus.SCHEDULED,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    origin: Mapped[Town] = relationship(foreign_keys=[origin_town_id])
    destination: Mapped[Town] = relationship(foreign_keys=[destination_town_id])
    bus: Mapped[Bus] = relationship()
