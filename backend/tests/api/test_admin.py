"""Admin endpoints (PLAN §7.6)."""

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.domain.trip_status import TripStatus
from tests.factories import bus, make_trip


def test_transition(client: TestClient, db: Session) -> None:
    trip = make_trip(db)
    url = f"/api/v1/admin/trips/{trip.id}/transitions"
    ok = client.post(url, json={"to_status": "boarding"})
    assert (ok.status_code, ok.json()["status"]) == (200, "boarding")
    skip = client.post(url, json={"to_status": "arrived"})
    assert (skip.status_code, skip.json()["code"]) == (409, "invalid-transition")
    bad = client.post(url, json={"to_status": "teleported"})
    assert bad.status_code == 422
    missing = client.post(
        "/api/v1/admin/trips/00000000-0000-0000-0000-000000000000/transitions",
        json={"to_status": "boarding"},
    )
    assert missing.status_code == 404


def test_bus_crud(client: TestClient) -> None:
    created = client.post(
        "/api/v1/admin/buses", json={"plate_number": "abc-123", "capacity": 18}
    )
    assert created.status_code == 201
    assert created.json()["plate_number"] == "ABC-123"
    dup = client.post(
        "/api/v1/admin/buses", json={"plate_number": "ABC-123", "capacity": 18}
    )
    assert (dup.status_code, dup.json()["code"]) == (409, "duplicate-plate")
    zero = client.post(
        "/api/v1/admin/buses", json={"plate_number": "Z-1", "capacity": 0}
    )
    assert zero.status_code == 422

    bus_id = created.json()["id"]
    patched = client.patch(f"/api/v1/admin/buses/{bus_id}", json={"active": False})
    assert patched.json()["active"] is False
    assert client.patch("/api/v1/admin/buses/999999", json={}).status_code == 404
    plates = [b["plate_number"] for b in client.get("/api/v1/admin/buses").json()]
    assert "ABC-123" in plates


def test_reassign(client: TestClient, db: Session) -> None:
    trip = make_trip(db, bus_plate="TEST-001", seats_booked=10)
    small = bus(db, "TEST-003")
    ok = client.put(f"/api/v1/admin/trips/{trip.id}/bus", json={"bus_id": small.id})
    assert (ok.status_code, ok.json()["capacity"]) == (200, 40)

    full = make_trip(db, bus_plate="TEST-001", seats_booked=42)
    too_small = client.put(
        f"/api/v1/admin/trips/{full.id}/bus", json={"bus_id": small.id}
    )
    assert (too_small.status_code, too_small.json()["seats_booked"]) == (409, 42)

    gone = make_trip(db, status=TripStatus.DEPARTED)
    late = client.put(f"/api/v1/admin/trips/{gone.id}/bus", json={"bus_id": small.id})
    assert (late.status_code, late.json()["code"]) == (409, "trip-not-reassignable")

    nobus = client.put(f"/api/v1/admin/trips/{trip.id}/bus", json={"bus_id": 999999})
    assert nobus.status_code == 404


def test_reconciliation_is_clean(client: TestClient, db: Session) -> None:
    make_trip(db)
    body = client.get("/api/v1/admin/reconciliation").json()
    assert body["drifted"] == []
    assert body["checked_at"]


def test_admin_is_documented_as_trusted_only(client: TestClient) -> None:
    spec = client.get("/api/v1/openapi.json").json()
    admin = next(t for t in spec["tags"] if t["name"] == "admin")
    assert "Trusted-only" in admin["description"]
