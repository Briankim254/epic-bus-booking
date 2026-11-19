import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.api.deps import SessionDep, TripServiceDep, require_admin
from app.api.routes._responses import problems
from app.schemas.admin import DriftReport
from app.schemas.trip import BusAssignIn, TransitionIn, TripOut, TripPage, TripQuery
from app.services import reconciliation

router = APIRouter(
    prefix="/admin", tags=["admin"], dependencies=[Depends(require_admin)]
)


@router.get("/trips", response_model=TripPage, responses=problems(422))
def admin_search_trips(
    service: TripServiceDep, query: Annotated[TripQuery, Query()]
) -> TripPage:
    """Every trip in every status, with how full it is."""
    return service.search(query, bookable_only=False)


@router.post(
    "/trips/{trip_id}/transitions",
    response_model=TripOut,
    responses=problems(404, 409, 422),
)
def transition_trip(
    service: TripServiceDep, trip_id: uuid.UUID, body: TransitionIn
) -> TripOut:
    """Move a trip one step along scheduled → boarding → … → completed."""
    return service.transition(trip_id, body.to_status)


@router.put(
    "/trips/{trip_id}/bus", response_model=TripOut, responses=problems(404, 409, 422)
)
def assign_bus(
    service: TripServiceDep, trip_id: uuid.UUID, body: BusAssignIn
) -> TripOut:
    """Move a scheduled trip to another active bus with enough seats (A9, A10)."""
    return service.assign_bus(trip_id, body.bus_id)


@router.get("/reconciliation", response_model=DriftReport)
def get_reconciliation(session: SessionDep) -> DriftReport:
    """Trips whose seat counter disagrees with their bookings. Should always be empty."""
    return reconciliation.report(session)
