"""Fare rules from the brief (PLAN §7.1). Pure: no database."""

from itertools import product

import pytest
from app.domain.errors import FareNotConfigured, SameTownError
from app.domain.fares import TownRef, fare_for_zones, quote

from app.seed import FARES

# The brief's fare table, written out in full (all 16 ordered pairs) and independently of
# the seed's 10-row storage, so a typo in either one fails a test. US cents.
BRIEF = {
    1: {1: 800, 2: 1800, 3: 2500, 4: 3500},
    2: {1: 1800, 2: 1000, 3: 1800, 4: 2800},
    3: {1: 2500, 2: 1800, 3: 800, 4: 2200},
    4: {1: 3500, 2: 2800, 3: 2200, 4: 800},
}

LAGOS = TownRef(id=1, zone_id=1)
IBADAN = TownRef(id=2, zone_id=1)
ABUJA = TownRef(id=5, zone_id=3)


@pytest.mark.parametrize(("a", "b"), list(product(range(1, 5), repeat=2)))
def test_every_ordered_zone_pair_matches_the_brief(a: int, b: int) -> None:
    assert fare_for_zones(a, b, FARES) == BRIEF[a][b]


@pytest.mark.parametrize(("a", "b"), list(product(range(1, 5), repeat=2)))
def test_fares_are_symmetric(a: int, b: int) -> None:
    assert fare_for_zones(a, b, FARES) == fare_for_zones(b, a, FARES)


def test_quote_prices_a_journey_by_the_towns_zones() -> None:
    assert quote(LAGOS, ABUJA, FARES) == 2500
    assert quote(ABUJA, LAGOS, FARES) == 2500


def test_same_zone_different_towns_is_priced() -> None:
    assert quote(LAGOS, IBADAN, FARES) == 800


def test_same_town_is_rejected() -> None:
    with pytest.raises(SameTownError):
        quote(LAGOS, LAGOS, FARES)


def test_missing_table_entry_is_reported() -> None:
    partial = {k: v for k, v in FARES.items() if k != (1, 3)}
    with pytest.raises(FareNotConfigured):
        quote(LAGOS, ABUJA, partial)
