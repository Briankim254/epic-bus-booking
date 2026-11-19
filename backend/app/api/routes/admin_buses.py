from fastapi import APIRouter, Depends, status

from app.api.deps import BusServiceDep, require_admin
from app.api.routes._responses import problems
from app.schemas.bus import BusIn, BusOut, BusPatch

router = APIRouter(
    prefix="/admin/buses", tags=["admin"], dependencies=[Depends(require_admin)]
)


@router.get("", response_model=list[BusOut])
def list_buses(service: BusServiceDep) -> list[BusOut]:
    return service.list()


@router.post(
    "",
    response_model=BusOut,
    status_code=status.HTTP_201_CREATED,
    responses=problems(409, 422),
)
def create_bus(service: BusServiceDep, body: BusIn) -> BusOut:
    return service.create(body)


@router.patch("/{bus_id}", response_model=BusOut, responses=problems(404, 422))
def update_bus(service: BusServiceDep, bus_id: int, body: BusPatch) -> BusOut:
    """Change name, capacity or active. Trips already on this bus keep their capacity."""
    return service.update(bus_id, body)
