"""Trip lifecycle rules. Pure: no imports from the rest of the app.

Nothing else in the codebase compares statuses; ask this module instead.
"""

from collections.abc import Mapping
from enum import StrEnum


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

BOOKABLE: frozenset[TripStatus] = frozenset({TripStatus.SCHEDULED})


class InvalidTransition(Exception):
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
