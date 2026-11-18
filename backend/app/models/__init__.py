"""Import every model module here, or Alembic autogenerate will not see its tables."""

from app.models.base import Base

__all__ = ["Base"]
