from typing import Annotated

from fastapi import APIRouter, Query

from app.api.deps import ReferenceDataDep
from app.api.routes._responses import problems
from app.schemas.town import FareQuote

router = APIRouter(prefix="/fares", tags=["fares"])


@router.get("/quote", response_model=FareQuote, responses=problems(404, 422))
def quote_fare(
    service: ReferenceDataDep,
    origin_town_id: Annotated[int, Query(ge=1)],
    destination_town_id: Annotated[int, Query(ge=1)],
) -> FareQuote:
    """Price a journey. The fare is per seat and depends only on the two towns' zones."""
    return service.quote(origin_town_id, destination_town_id)
