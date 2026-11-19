from app.schemas.common import Currency, ORMModel


class TownOut(ORMModel):
    id: int
    name: str
    zone_id: int


class FareQuote(ORMModel):
    origin: TownOut
    destination: TownOut
    fare_cents: int
    currency: Currency = "USD"
