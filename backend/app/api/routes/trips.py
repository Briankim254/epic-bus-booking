import uuid
from typing import Annotated

from fastapi import APIRouter, Query

from app.api.deps import TripServiceDep
from app.api.routes._responses import problems
from app.schemas.trip import TripOut, TripPage, TripQuery

router = APIRouter(prefix="/trips", tags=["trips"])


@router.get("", response_model=TripPage, responses=problems(422))
def search_trips(
    service: TripServiceDep, query: Annotated[TripQuery, Query()]
) -> TripPage:
    """Bookable trips only: scheduled, departing in the future, with a seat left."""
    return service.search(query, bookable_only=True)


@router.get("/{trip_id}", response_model=TripOut, responses=problems(404))
def get_trip(service: TripServiceDep, trip_id: uuid.UUID) -> TripOut:
    return service.get(trip_id)
