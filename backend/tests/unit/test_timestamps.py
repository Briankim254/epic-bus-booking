"""Guard: every model gets its timestamps from models/mixins.py, so none can be forgotten."""

from app.models import Base
from app.models.mixins import CreatedAtMixin, TimestampMixin

# Reference data has no timestamps; history rows carry their own `changed_at`.
EXEMPT = {"zones", "towns", "zone_fares", "trip_status_history"}


def test_every_model_uses_a_timestamp_mixin() -> None:
    missing = [
        m.class_.__name__
        for m in Base.registry.mappers
        if m.local_table.name not in EXEMPT and not issubclass(m.class_, CreatedAtMixin)
    ]
    assert missing == []


def test_every_updated_at_column_moves_on_update() -> None:
    for table in Base.metadata.sorted_tables:
        column = table.columns.get("updated_at")
        if column is not None:
            assert column.onupdate is not None, table.name


def test_mutable_models_have_updated_at() -> None:
    for m in Base.registry.mappers:
        if issubclass(m.class_, TimestampMixin):
            assert "updated_at" in m.local_table.columns
