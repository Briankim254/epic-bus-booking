"""Dependency injection: each route asks for one service, built on the request's session."""

from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session

from app.core.db import get_session
from app.services.booking_service import BookingService
from app.services.bus_service import BusService
from app.services.reference_data import ReferenceDataService
from app.services.trip_service import TripService

SessionDep = Annotated[Session, Depends(get_session)]


def require_admin() -> None:
    """No-op by design: the brief excludes auth.

    This is the single seam where OIDC/JWT with an admin role claim would be enforced.
    """


def get_booking_service(session: SessionDep) -> BookingService:
    return BookingService(session)


def get_trip_service(session: SessionDep) -> TripService:
    return TripService(session)


def get_bus_service(session: SessionDep) -> BusService:
    return BusService(session)


def get_reference_data_service(session: SessionDep) -> ReferenceDataService:
    return ReferenceDataService(session)


BookingServiceDep = Annotated[BookingService, Depends(get_booking_service)]
TripServiceDep = Annotated[TripService, Depends(get_trip_service)]
BusServiceDep = Annotated[BusService, Depends(get_bus_service)]
ReferenceDataDep = Annotated[ReferenceDataService, Depends(get_reference_data_service)]
