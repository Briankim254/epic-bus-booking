"""GET /trips and GET /admin/trips (PLAN §4, Search)."""

from datetime import UTC, datetime, timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.domain.lagos_time import LAGOS
from app.domain.trip_status import TripStatus
from tests.factories import make_trip, town_id


def _ids(r: object) -> list[str]:
    return [t["id"] for t in r.json()["items"]]  # type: ignore[attr-defined]


def test_public_search_hides_unbookable_trips(client: TestClient, db: Session) -> None:
    open_trip = make_trip(db)
    make_trip(db, status=TripStatus.DEPARTED)
    make_trip(db, capacity=44, seats_booked=44)  # full
    make_trip(db, departs_in=timedelta(hours=-1))  # departed by the clock

    public = client.get("/api/v1/trips")
    assert public.status_code == 200
    assert _ids(public) == [str(open_trip.id)]
    assert public.json()["total"] == 1

    admin = client.get("/api/v1/admin/trips")
    assert admin.json()["total"] == 4


def test_filters_by_origin_and_destination(client: TestClient, db: Session) -> None:
    lag_abj = make_trip(db, origin="Lagos", destination="Abuja")
    make_trip(db, origin="Abuja", destination="Lagos")
    make_trip(db, origin="Lagos", destination="Kano")
    r = client.get(
        "/api/v1/trips",
        params={
            "origin_town_id": town_id(db, "Lagos"),
            "destination_town_id": town_id(db, "Abuja"),
        },
    )
    assert _ids(r) == [str(lag_abj.id)]


def test_date_is_a_lagos_calendar_day(client: TestClient, db: Session) -> None:
    """23:30 UTC is 00:30 the next day in Lagos (UTC+1)."""
    day = (datetime.now(LAGOS) + timedelta(days=3)).date()
    late_utc = datetime(day.year, day.month, day.day, 23, 30, tzinfo=UTC)
    trip = make_trip(db, departs_at=late_utc)

    same_utc_day = client.get("/api/v1/trips", params={"date": day.isoformat()})
    next_day = client.get(
        "/api/v1/trips", params={"date": (day + timedelta(days=1)).isoformat()}
    )
    assert _ids(same_utc_day) == []
    assert _ids(next_day) == [str(trip.id)]


def test_sorts(client: TestClient, db: Session) -> None:
    soon_expensive = make_trip(
        db, origin="Lagos", destination="Kano", departs_in=timedelta(hours=1)
    )  # $35
    later_cheap = make_trip(
        db, origin="Lagos", destination="Ibadan", departs_in=timedelta(hours=5)
    )  # $8
    by = {
        s: _ids(client.get("/api/v1/trips", params={"sort": s}))
        for s in ("departs_at", "-departs_at", "price", "-price")
    }
    a, b = str(soon_expensive.id), str(later_cheap.id)
    assert by == {
        "departs_at": [a, b],
        "-departs_at": [b, a],
        "price": [b, a],
        "-price": [a, b],
    }


@pytest.mark.parametrize(
    "params",
    [
        {"sort": "evil"},
        {"sort": "departs_at; DROP TABLE trips"},
        {"limit": 101},
        {"limit": 0},
        {"offset": -1},
        {"date": "18/11/2026"},
    ],
)
def test_bad_parameters_are_422(client: TestClient, params: dict[str, object]) -> None:
    r = client.get("/api/v1/trips", params=params)
    assert r.status_code == 422
    assert r.headers["content-type"].startswith("application/problem+json")


def test_pagination_is_stable(client: TestClient, db: Session) -> None:
    same_time = datetime.now(UTC) + timedelta(hours=3)
    for _ in range(5):
        make_trip(db, departs_at=same_time)  # identical sort keys: id breaks the tie
    pages = [
        _ids(client.get("/api/v1/trips", params={"limit": 2, "offset": o}))
        for o in (0, 2, 4)
    ]
    flat = [i for p in pages for i in p]
    assert [len(p) for p in pages] == [2, 2, 1]
    assert len(set(flat)) == 5
    assert pages[0] == _ids(client.get("/api/v1/trips", params={"limit": 2}))


def test_get_trip(client: TestClient, db: Session) -> None:
    trip = make_trip(db, origin="Enugu", destination="Abuja")  # zones 2 -> 3: $18
    body = client.get(f"/api/v1/trips/{trip.id}").json()
    assert (body["fare_cents"], body["seats_available"]) == (1800, trip.capacity)
    missing = client.get("/api/v1/trips/00000000-0000-0000-0000-000000000000")
    assert (missing.status_code, missing.json()["code"]) == (404, "trip-not-found")
