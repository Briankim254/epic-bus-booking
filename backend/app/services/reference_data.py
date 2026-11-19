from sqlalchemy.orm import Session

from app.domain.errors import TownNotFound
from app.domain.fares import TownRef, quote
from app.repositories.fares import FareRepository
from app.schemas.town import FareQuote, TownOut


class ReferenceDataService:
    """Towns and fare quotes: read-only reference data."""

    def __init__(self, session: Session) -> None:
        self._fares = FareRepository(session)

    def list_towns(self) -> list[TownOut]:
        return [TownOut.model_validate(t) for t in self._fares.list_towns()]

    def quote(self, origin_town_id: int, destination_town_id: int) -> FareQuote:
        towns = self._fares.get_towns([origin_town_id, destination_town_id])
        if origin_town_id not in towns or destination_town_id not in towns:
            raise TownNotFound
        o, d = towns[origin_town_id], towns[destination_town_id]
        fare = quote(
            TownRef(o.id, o.zone_id), TownRef(d.id, d.zone_id), self._fares.load_table()
        )
        return FareQuote(
            origin=TownOut.model_validate(o),
            destination=TownOut.model_validate(d),
            fare_cents=fare,
        )
