from fastapi import APIRouter
from pydantic import BaseModel
from sqlalchemy import text

from app.api.deps import SessionDep

router = APIRouter(prefix="/health", tags=["health"])


class HealthOut(BaseModel):
    status: str


@router.get("", response_model=HealthOut)
def health_check(session: SessionDep) -> HealthOut:
    session.execute(text("SELECT 1"))
    return HealthOut(status="ok")
