from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from tests.factories import town_id


def test_towns(client: TestClient) -> None:
    names = [t["name"] for t in client.get("/api/v1/towns").json()]
    assert sorted(names) == ["Abuja", "Enugu", "Ibadan", "Kano", "Lagos", "Onitsha"]


def test_quote(client: TestClient, db: Session) -> None:
    lagos, abuja = town_id(db, "Lagos"), town_id(db, "Abuja")
    r = client.get(
        "/api/v1/fares/quote",
        params={"origin_town_id": lagos, "destination_town_id": abuja},
    )
    assert r.status_code == 200
    assert (r.json()["fare_cents"], r.json()["currency"]) == (2500, "USD")

    same = client.get(
        "/api/v1/fares/quote",
        params={"origin_town_id": lagos, "destination_town_id": lagos},
    )
    assert (same.status_code, same.json()["code"]) == (422, "same-town")

    unknown = client.get(
        "/api/v1/fares/quote",
        params={"origin_town_id": lagos, "destination_town_id": 999},
    )
    assert (unknown.status_code, unknown.json()["code"]) == (404, "town-not-found")
