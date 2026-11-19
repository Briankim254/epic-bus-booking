"""POST /bookings and GET /bookings/{reference} over HTTP (PLAN §7.6)."""

import logging
import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from tests.factories import make_trip

PROBLEM = "application/problem+json"


def _post(
    client: TestClient,
    trip_id: object,
    name: object = "Bola",
    seats: object = 1,
    key: str | None = None,
) -> object:
    headers = {"Idempotency-Key": key} if key else {}
    return client.post(
        "/api/v1/bookings",
        json={"trip_id": str(trip_id), "passenger_name": name, "seats": seats},
        headers=headers,
    )


@pytest.mark.parametrize("seats", [0, -1, 11, "two", 1.5])
def test_bad_seat_counts_are_422(
    client: TestClient, db: Session, seats: object
) -> None:
    trip = make_trip(db)
    r = client.post(
        "/api/v1/bookings",
        json={"trip_id": str(trip.id), "passenger_name": "Bola", "seats": seats},
    )
    assert r.status_code == 422
    assert r.headers["content-type"].startswith(PROBLEM)
    assert r.json()["code"] == "validation-error"


@pytest.mark.parametrize(
    "name", ["", "   ", "x" * 101, "Bola\u0000Ade", "Bola\nAde", "Bola‮Ade"]
)
def test_bad_names_are_422_and_never_echoed(
    client: TestClient, db: Session, name: str
) -> None:
    trip = make_trip(db)
    r = client.post(
        "/api/v1/bookings",
        json={"trip_id": str(trip.id), "passenger_name": name, "seats": 1},
    )
    assert r.status_code == 422
    if name.strip():
        assert name not in r.text


@pytest.mark.parametrize(
    "name", ["Ọláyíwọlá Chukwuémeká", "Ngọzi", "Ifeoma O'Neil-Okeke", "  Musa  "]
)
def test_real_names_round_trip(client: TestClient, db: Session, name: str) -> None:
    trip = make_trip(db)
    r = client.post(
        "/api/v1/bookings",
        json={"trip_id": str(trip.id), "passenger_name": name, "seats": 1},
    )
    assert r.status_code == 201, r.text
    body = r.json()
    assert body["passenger_name"] == name.strip()
    looked_up = client.get(f"/api/v1/bookings/{body['reference']}").json()
    assert looked_up["passenger_name"] == name.strip()


def test_booking_response_shape(client: TestClient, db: Session) -> None:
    trip = make_trip(db, origin="Lagos", destination="Kano")  # zones 1 -> 4: $35
    r = client.post(
        "/api/v1/bookings",
        json={"trip_id": str(trip.id), "passenger_name": "Musa", "seats": 2},
    )
    assert r.status_code == 201
    body = r.json()
    assert (body["seats"], body["fare_cents_per_seat"], body["total_cents"]) == (
        2,
        3500,
        7000,
    )
    assert body["trip"]["seats_booked"] == 2
    assert body["trip"]["currency"] == "USD"
    assert body["trip"]["bus"]["plate_number"] == "TEST-001"


def test_insufficient_seats_is_409_with_remaining(
    client: TestClient, db: Session
) -> None:
    trip = make_trip(db, capacity=44, seats_booked=43)
    r = client.post(
        "/api/v1/bookings",
        json={"trip_id": str(trip.id), "passenger_name": "Musa", "seats": 2},
    )
    assert r.status_code == 409
    assert r.headers["content-type"].startswith(PROBLEM)
    body = r.json()
    assert (body["code"], body["remaining"]) == ("insufficient-seats", 1)
    assert body["request_id"]


def test_unknown_trip_is_404(client: TestClient) -> None:
    r = client.post(
        "/api/v1/bookings",
        json={"trip_id": str(uuid.uuid4()), "passenger_name": "Musa", "seats": 1},
    )
    assert (r.status_code, r.json()["code"]) == (404, "trip-not-found")


def test_idempotent_replay_over_http(client: TestClient, db: Session) -> None:
    trip = make_trip(db)
    payload = {"trip_id": str(trip.id), "passenger_name": "Musa", "seats": 1}
    key = {"Idempotency-Key": str(uuid.uuid4())}
    first = client.post("/api/v1/bookings", json=payload, headers=key)
    again = client.post("/api/v1/bookings", json=payload, headers=key)
    assert first.status_code == again.status_code == 201
    assert "Idempotent-Replayed" not in first.headers
    assert again.headers["Idempotent-Replayed"] == "true"
    assert again.json() == first.json()

    payload["seats"] = 2
    reused = client.post("/api/v1/bookings", json=payload, headers=key)
    assert (reused.status_code, reused.json()["code"]) == (
        422,
        "idempotency-key-reused",
    )


def test_unknown_reference_is_404(client: TestClient) -> None:
    r = client.get("/api/v1/bookings/BK-0000-0000")
    assert (r.status_code, r.json()["code"]) == (404, "booking-not-found")


def test_passenger_names_never_reach_the_logs(
    client: TestClient, db: Session, caplog: pytest.LogCaptureFixture
) -> None:
    trip = make_trip(db)
    distinctive = "Zzyzx Qwertyuiopasdf"
    app_logger = logging.getLogger("app")
    app_logger.addHandler(caplog.handler)
    try:
        with caplog.at_level(logging.DEBUG, logger="app"):
            ok = client.post(
                "/api/v1/bookings",
                json={
                    "trip_id": str(trip.id),
                    "passenger_name": distinctive,
                    "seats": 1,
                },
            )
            bad = client.post(
                "/api/v1/bookings",
                json={
                    "trip_id": str(trip.id),
                    "passenger_name": distinctive,
                    "seats": 0,
                },
            )
    finally:
        app_logger.removeHandler(caplog.handler)
    assert (ok.status_code, bad.status_code) == (201, 422)
    assert any(r.getMessage() == "booking.created" for r in caplog.records)
    for record in caplog.records:
        assert distinctive not in record.getMessage()
        assert distinctive not in str(record.__dict__)
    assert ok.json()["reference"] not in caplog.text
