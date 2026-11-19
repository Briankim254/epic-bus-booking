from sqlalchemy import CheckConstraint, ForeignKey, SmallInteger, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class Zone(Base):
    __tablename__ = "zones"

    id: Mapped[int] = mapped_column(SmallInteger, primary_key=True, autoincrement=False)
    name: Mapped[str] = mapped_column(String(50), unique=True)


class Town(Base):
    __tablename__ = "towns"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=False)
    name: Mapped[str] = mapped_column(String(50), unique=True)
    zone_id: Mapped[int] = mapped_column(SmallInteger, ForeignKey("zones.id"))

    zone: Mapped[Zone] = relationship()


class ZoneFare(Base):
    """One row per unordered zone pair (10 rows for 4 zones): symmetry by construction."""

    __tablename__ = "zone_fares"
    __table_args__ = (
        CheckConstraint("zone_a_id <= zone_b_id", name="ordered"),
        CheckConstraint("fare_cents > 0", name="positive"),
    )

    zone_a_id: Mapped[int] = mapped_column(
        SmallInteger, ForeignKey("zones.id"), primary_key=True
    )
    zone_b_id: Mapped[int] = mapped_column(
        SmallInteger, ForeignKey("zones.id"), primary_key=True
    )
    fare_cents: Mapped[int]
