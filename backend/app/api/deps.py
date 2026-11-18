from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session

from app.core.db import get_session

SessionDep = Annotated[Session, Depends(get_session)]


def require_admin() -> None:
    """No-op by design: the brief excludes auth.

    This is the single seam where OIDC/JWT with an admin role claim would be enforced.
    """
