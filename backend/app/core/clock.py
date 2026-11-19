from datetime import UTC, datetime


def utcnow() -> datetime:
    """The default clock. Services take it as a parameter so tests can move time."""
    return datetime.now(UTC)
