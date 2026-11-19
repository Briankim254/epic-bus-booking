from typing import Annotated

from fastapi import APIRouter, Header, Path, Response, status

from app.api.deps import BookingServiceDep
from app.api.routes._responses import problems
from app.schemas.booking import BookingIn, BookingOut

router = APIRouter(prefix="/bookings", tags=["bookings"])

IdempotencyKey = Annotated[
    str | None,
    Header(
        alias="Idempotency-Key",
        min_length=1,
        max_length=255,
        description="Send a fresh UUID per booking attempt; a retry with the same key "
        "returns the original booking instead of booking twice.",
    ),
]


@router.post(
    "",
    response_model=BookingOut,
    status_code=status.HTTP_201_CREATED,
    responses=problems(404, 409, 422),
)
def create_booking(
    service: BookingServiceDep,
    body: BookingIn,
    response: Response,
    idempotency_key: IdempotencyKey = None,
) -> BookingOut:
    result = service.create(body, idempotency_key=idempotency_key)
    if result.replayed:
        response.headers["Idempotent-Replayed"] = "true"
    return result.booking


@router.get("/{reference}", response_model=BookingOut, responses=problems(404))
def get_booking(
    service: BookingServiceDep,
    reference: Annotated[str, Path(min_length=12, max_length=12)],
) -> BookingOut:
    return service.get(reference.upper())
