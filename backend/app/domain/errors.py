"""Domain errors. Pure: no FastAPI, no SQLAlchemy.

Each error carries a stable `code` and an HTTP-ish `status`, and core/errors.py turns it
into application/problem+json in one handler. Services raise these; routes never catch them.
`extra()` holds fields that are safe to return (never submitted input such as names).
"""

from typing import Any, ClassVar


class DomainError(Exception):
    code: ClassVar[str] = "domain-error"
    status: ClassVar[int] = 400
    title: ClassVar[str] = "Request could not be completed"

    def __init__(self, detail: str | None = None) -> None:
        super().__init__(detail or self.title)
        self.detail = detail

    def extra(self) -> dict[str, Any]:
        return {}


class NotFound(DomainError):
    status = 404


class Conflict(DomainError):
    status = 409


class TripNotFound(NotFound):
    code = "trip-not-found"
    title = "Trip not found"


class BookingNotFound(NotFound):
    code = "booking-not-found"
    title = "Booking not found"


class BusNotFound(NotFound):
    code = "bus-not-found"
    title = "Bus not found"


class TownNotFound(NotFound):
    code = "town-not-found"
    title = "Town not found"


class TripNotBookable(Conflict):
    code = "trip-not-bookable"
    title = "Trip is not open for booking"


class InsufficientSeats(Conflict):
    code = "insufficient-seats"
    title = "Not enough seats"

    def __init__(self, requested: int, remaining: int) -> None:
        super().__init__(f"{requested} seats requested, {remaining} remaining.")
        self.requested = requested
        self.remaining = remaining

    def extra(self) -> dict[str, Any]:
        return {"remaining": self.remaining}


class StaleStatus(Conflict):
    code = "stale-status"
    title = "Trip status changed; reload and try again"


class BusInactive(Conflict):
    code = "bus-inactive"
    title = "Bus is not active"


class BusTooSmall(Conflict):
    code = "bus-too-small"
    title = "Bus has fewer seats than are already booked"

    def __init__(self, capacity: int, seats_booked: int) -> None:
        super().__init__(f"Bus has {capacity} seats; {seats_booked} are booked.")
        self.capacity = capacity
        self.seats_booked = seats_booked

    def extra(self) -> dict[str, Any]:
        return {"seats_booked": self.seats_booked}


class DuplicatePlate(Conflict):
    code = "duplicate-plate"
    title = "A bus with this plate number already exists"


class IdempotencyKeyReused(DomainError):
    code = "idempotency-key-reused"
    status = 422
    title = "Idempotency-Key was already used with a different request"


class SameTownError(DomainError):
    code = "same-town"
    status = 422
    title = "Origin and destination must be different towns"


class FareNotConfigured(DomainError):
    code = "fare-not-configured"
    status = 500
    title = "No fare is configured for this journey"
