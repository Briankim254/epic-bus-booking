"""Trip state machine (PLAN §7.2): all 36 (from, to) pairs, exactly 5 allowed."""

from itertools import product

import pytest
from app.domain.errors import DomainError

from app.domain.trip_status import (
    BOOKABLE,
    InvalidTransition,
    TripStatus,
    assert_transition,
    path_to,
)

S = TripStatus
ALLOWED = {
    (S.SCHEDULED, S.BOARDING),
    (S.BOARDING, S.DEPARTED),
    (S.DEPARTED, S.IN_TRANSIT),
    (S.IN_TRANSIT, S.ARRIVED),
    (S.ARRIVED, S.COMPLETED),
}


@pytest.mark.parametrize(("current", "target"), list(product(S, repeat=2)))
def test_only_the_five_forward_steps_are_allowed(
    current: TripStatus, target: TripStatus
) -> None:
    if (current, target) in ALLOWED:
        assert_transition(current, target)
    else:
        with pytest.raises(InvalidTransition):
            assert_transition(current, target)


def test_invalid_transition_is_a_domain_error_with_a_code() -> None:
    with pytest.raises(DomainError) as exc:
        assert_transition(S.SCHEDULED, S.ARRIVED)
    assert exc.value.code == "invalid-transition"
    assert exc.value.status == 409


def test_only_scheduled_is_bookable() -> None:
    assert BOOKABLE == {S.SCHEDULED}


def test_path_to_walks_every_step() -> None:
    assert path_to(S.ARRIVED) == [S.BOARDING, S.DEPARTED, S.IN_TRANSIT, S.ARRIVED]
    assert path_to(S.SCHEDULED) == []
