"""Booking rules that need no database. Pure."""

import hashlib
import json
import uuid

MAX_SEATS_PER_BOOKING = 10  # assumption A5; the brief is silent


def request_hash(trip_id: uuid.UUID, passenger_name: str, seats: int) -> str:
    """sha256 of the canonical booking request, for Idempotency-Key replay checks."""
    canonical = json.dumps(
        {"trip_id": str(trip_id), "passenger_name": passenger_name, "seats": seats},
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    )
    return hashlib.sha256(canonical.encode()).hexdigest()
