"""Booking: one transaction, all or nothing (PLAN §5, "Booking flow").

  1. Claim the Idempotency-Key (if sent). A replay returns the stored response.
  2. Reserve seats with the conditional UPDATE (no overbooking, bookable, future).
  3. Price the journey with the pure fare function.
  4. Insert the booking with a fare snapshot and a fresh reference (retried on collision).
  5. Store the response on the key row and commit.
Any failure rolls back everything, including the key claim, so a retry re-evaluates.
"""

import logging
import uuid
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime

from sqlalchemy.orm import Session

from app.core.clock import utcnow
from app.domain.booking_rules import request_hash
from app.domain.errors import (
    BookingNotFound,
    IdempotencyKeyReused,
    InsufficientSeats,
    TripNotBookable,
    TripNotFound,
)
from app.domain.fares import quote
from app.domain.references import generate_reference
from app.domain.trip_status import BOOKABLE
from app.models import Booking
from app.repositories.bookings import BookingRepository
from app.repositories.fares import FareRepository
from app.repositories.idempotency import IdempotencyRepository
from app.repositories.trips import TripRepository
from app.schemas.booking import BookingIn, BookingOut
from app.schemas.trip import TripOut

logger = logging.getLogger("app.bookings")

SCOPE = "bookings.create"
REFERENCE_ATTEMPTS = 3


@dataclass(frozen=True)
class BookingResult:
    booking: BookingOut
    replayed: bool


class BookingService:
    def __init__(
        self,
        session: Session,
        *,
        clock: Callable[[], datetime] = utcnow,
        new_reference: Callable[[], str] = generate_reference,
    ) -> None:
        self._s = session
        self._clock = clock
        self._new_reference = new_reference
        self._trips = TripRepository(session)
        self._bookings = BookingRepository(session)
        self._fares = FareRepository(session)
        self._keys = IdempotencyRepository(session)

    def create(
        self, request: BookingIn, *, idempotency_key: str | None = None
    ) -> BookingResult:
        try:
            result = self._create(request, idempotency_key)
        except BaseException:
            self._s.rollback()
            raise
        self._s.commit()
        return result

    def get(self, reference: str) -> BookingOut:
        booking = self._bookings.get_by_reference(reference)
        if booking is None:
            raise BookingNotFound
        row = self._trips.get_row(booking.trip_id)
        assert row is not None  # FK guarantees the trip exists
        return _to_out(booking, TripOut.from_row(row))

    def _create(self, req: BookingIn, key: str | None) -> BookingResult:
        if key is not None:
            digest = request_hash(req.trip_id, req.passenger_name, req.seats)
            if not self._keys.claim(SCOPE, key, digest):
                return self._replay(key, digest)

        if not self._trips.reserve_seats(req.trip_id, req.seats, self._clock()):
            raise self._why_not(req.trip_id, req.seats)

        trip = self._trips.get(req.trip_id)
        assert trip is not None
        towns = self._fares.town_refs([trip.origin_town_id, trip.destination_town_id])
        fare = quote(
            towns[trip.origin_town_id],
            towns[trip.destination_town_id],
            self._fares.load_table(),
        )

        booking = self._insert(req, fare)
        row = self._trips.get_row(req.trip_id)
        assert row is not None
        out = _to_out(booking, TripOut.from_row(row))

        if key is not None:
            self._keys.store_response(SCOPE, key, 201, out.model_dump(mode="json"))
        logger.info(
            "booking.created",
            extra={
                "booking_id": str(booking.id),
                "trip_id": str(req.trip_id),
                "seats": req.seats,
                "total_cents": booking.total_cents,
            },
        )
        return BookingResult(out, replayed=False)

    def _insert(self, req: BookingIn, fare: int) -> Booking:
        for _ in range(REFERENCE_ATTEMPTS):
            booking = Booking(
                reference=self._new_reference(),
                trip_id=req.trip_id,
                passenger_name=req.passenger_name,
                seats=req.seats,
                fare_cents_per_seat=fare,
                total_cents=fare * req.seats,
            )
            if self._bookings.insert(booking):
                return booking
        raise RuntimeError("could not allocate a unique booking reference")

    def _replay(self, key: str, digest: str) -> BookingResult:
        stored = self._keys.get(SCOPE, key)
        assert stored is not None and stored.response_body is not None
        if stored.request_hash != digest:
            raise IdempotencyKeyReused
        logger.info("idempotency.replayed", extra={"scope": SCOPE})
        return BookingResult(
            BookingOut.model_validate(stored.response_body), replayed=True
        )

    def _why_not(self, trip_id: uuid.UUID, seats: int) -> Exception:
        """Advisory diagnosis after the atomic UPDATE already said no."""
        trip = self._trips.get(trip_id)
        if trip is None:
            error: Exception = TripNotFound()
        elif trip.status not in BOOKABLE or trip.departs_at <= self._clock():
            error = TripNotBookable()
        else:
            error = InsufficientSeats(seats, trip.capacity - trip.seats_booked)
        logger.info(
            "booking.rejected",
            extra={"trip_id": str(trip_id), "reason": getattr(error, "code", "")},
        )
        return error


def _to_out(booking: Booking, trip: TripOut) -> BookingOut:
    return BookingOut(
        reference=booking.reference,
        trip=trip,
        passenger_name=booking.passenger_name,
        seats=booking.seats,
        fare_cents_per_seat=booking.fare_cents_per_seat,
        total_cents=booking.total_cents,
        created_at=booking.created_at,
    )
