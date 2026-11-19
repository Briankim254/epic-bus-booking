"""Trip lifecycle rules. Pure: imports nothing from the app except domain errors.

Nothing else in the codebase compares statuses; ask this module instead.
"""

from collections.abc import Mapping
from enum import StrEnum

from app.domain.errors import Conflict


class TripStatus(StrEnum):
    SCHEDULED = "scheduled"
    BOARDING = "boarding"
    DEPARTED = "departed"
    IN_TRANSIT = "in_transit"
    ARRIVED = "arrived"
    COMPLETED = "completed"


TRANSITIONS: Mapping[TripStatus, frozenset[TripStatus]] = {
    TripStatus.SCHEDULED: frozenset({TripStatus.BOARDING}),
    TripStatus.BOARDING: frozenset({TripStatus.DEPARTED}),
    TripStatus.DEPARTED: frozenset({TripStatus.IN_TRANSIT}),
    TripStatus.IN_TRANSIT: frozenset({TripStatus.ARRIVED}),
    TripStatus.ARRIVED: frozenset({TripStatus.COMPLETED}),
    TripStatus.COMPLETED: frozenset(),
}

# Only a scheduled trip can take bookings (A1) or move to another bus (A10).
BOOKABLE: frozenset[TripStatus] = frozenset({TripStatus.SCHEDULED})
REASSIGNABLE: frozenset[TripStatus] = frozenset({TripStatus.SCHEDULED})


class InvalidTransition(Conflict):
    code = "invalid-transition"
    title = "Trip status cannot change this way"

    def __init__(self, current: TripStatus, target: TripStatus) -> None:
        super().__init__(f"Cannot move a trip from {current} to {target}.")
        self.current = current
        self.target = target


def assert_transition(current: TripStatus, target: TripStatus) -> None:
    if target not in TRANSITIONS[current]:
        raise InvalidTransition(current, target)


def path_to(target: TripStatus) -> list[TripStatus]:
    """Statuses after SCHEDULED, in order, up to and including `target`."""
    order = list(TripStatus)
    return order[1 : order.index(target) + 1]
