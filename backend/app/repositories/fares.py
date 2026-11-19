from collections.abc import Iterable

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain.fares import FareTable, TownRef
from app.models import Town, ZoneFare


class FareRepository:
    def __init__(self, session: Session) -> None:
        self._s = session

    def load_table(self) -> FareTable:
        rows = self._s.execute(
            select(ZoneFare.zone_a_id, ZoneFare.zone_b_id, ZoneFare.fare_cents)
        )
        return {(a, b): cents for a, b, cents in rows}

    def town_refs(self, town_ids: Iterable[int]) -> dict[int, TownRef]:
        rows = self._s.execute(
            select(Town.id, Town.zone_id).where(Town.id.in_(set(town_ids)))
        )
        return {i: TownRef(id=i, zone_id=z) for i, z in rows}

    def list_towns(self) -> list[Town]:
        return list(self._s.scalars(select(Town).order_by(Town.name)))

    def get_towns(self, town_ids: Iterable[int]) -> dict[int, Town]:
        towns = self._s.scalars(select(Town).where(Town.id.in_(set(town_ids))))
        return {t.id: t for t in towns}
