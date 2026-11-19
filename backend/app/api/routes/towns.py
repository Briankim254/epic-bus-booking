from fastapi import APIRouter

from app.api.deps import ReferenceDataDep
from app.schemas.town import TownOut

router = APIRouter(prefix="/towns", tags=["towns"])


@router.get("", response_model=list[TownOut])
def list_towns(service: ReferenceDataDep) -> list[TownOut]:
    return service.list_towns()
