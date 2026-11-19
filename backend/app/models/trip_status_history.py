import uuid
from datetime import datetime

from sqlalchemy import BigInteger, CheckConstraint, DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column

from app.domain.trip_status import TripStatus
from app.models.base import Base
from app.models.trip import STATUS_VALUES_SQL, TRIP_STATUS_TYPE


class TripStatusHistory(Base):
    """Append-only audit of status changes, written in the transition's transaction."""

    __tablename__ = "trip_status_history"
    __table_args__ = (
        CheckConstraint(f"from_status IN ({STATUS_VALUES_SQL})", name="from_valid"),
        CheckConstraint(f"to_status IN ({STATUS_VALUES_SQL})", name="to_valid"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    trip_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("trips.id"), index=True)
    from_status: Mapped[TripStatus] = mapped_column(TRIP_STATUS_TYPE)
    to_status: Mapped[TripStatus] = mapped_column(TRIP_STATUS_TYPE)
    changed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
