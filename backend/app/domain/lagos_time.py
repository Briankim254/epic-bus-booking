"""Search dates are calendar days in Africa/Lagos (A3); storage is UTC. Pure."""

from datetime import UTC, date, datetime, time, timedelta
from zoneinfo import ZoneInfo

LAGOS = ZoneInfo("Africa/Lagos")


def lagos_day_bounds(day: date) -> tuple[datetime, datetime]:
    """[local midnight, next local midnight) for `day`, as UTC datetimes."""
    start = datetime.combine(day, time.min, LAGOS)
    end = datetime.combine(day + timedelta(days=1), time.min, LAGOS)
    return start.astimezone(UTC), end.astimezone(UTC)
