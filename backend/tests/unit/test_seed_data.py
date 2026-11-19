"""Guards on the seed constants, so a typo can't ship broken demo data. No database needed."""

from collections import Counter
from itertools import combinations_with_replacement

from app.domain.trip_status import TripStatus
from app.seed import BOOKINGS, BUSES, FARES, TOWNS, TRIPS

MAX_SEATS_PER_BOOKING = 10  # assumption A5


def test_six_towns_in_four_zones_as_in_the_brief() -> None:
    by_zone: dict[int, set[str]] = {}
    for name, zone in TOWNS.values():
        by_zone.setdefault(zone, set()).add(name)
    assert by_zone == {
        1: {"Lagos", "Ibadan"},
        2: {"Enugu", "Onitsha"},
        3: {"Abuja"},
        4: {"Kano"},
    }


def test_fare_table_covers_every_zone_pair_once() -> None:
    assert set(FARES) == set(combinations_with_replacement(range(1, 5), 2))
    assert FARES[(1, 3)] == 2500  # Lagos region <-> Middle Belt: $25


def _capacity(trip_key: str) -> int:
    """A trip's capacity is copied from its bus, so look it up the same way."""
    trip = next(t for t in TRIPS if t.key == trip_key)
    return BUSES[trip.bus][1]


def test_four_buses_two_of_each_size() -> None:
    assert Counter(cap for _, cap in BUSES.values()) == {40: 2, 44: 2}
    assert all(len(plate) <= 20 for plate in BUSES)


def test_no_bus_runs_two_trips_on_the_same_day() -> None:
    days = [(t.bus, t.day_offset) for t in TRIPS]
    assert len(days) == len(set(days))


def test_trips_match_the_brief() -> None:
    town_names = {name for name, _ in TOWNS.values()}
    assert 9 <= len(TRIPS) <= 12
    assert len({t.key for t in TRIPS}) == len(TRIPS)
    for t in TRIPS:
        assert {t.origin, t.destination} <= town_names
        assert t.origin != t.destination
        assert t.bus in BUSES
    statuses = Counter(t.final_status for t in TRIPS)
    assert statuses[TripStatus.SCHEDULED] >= 7
    assert {TripStatus.DEPARTED, TripStatus.ARRIVED} <= set(statuses)


def test_bookings_fit_their_trips() -> None:
    capacity = {t.key: _capacity(t.key) for t in TRIPS}
    booked: Counter[str] = Counter()
    for key, name, seats in BOOKINGS:
        assert key in capacity
        assert name.strip()
        assert 1 <= seats <= MAX_SEATS_PER_BOOKING
        booked[key] += seats
    assert 13 <= len(BOOKINGS) <= 17
    assert all(booked[k] <= capacity[k] for k in booked)


def test_one_scheduled_trip_is_left_with_exactly_one_seat() -> None:
    capacity = {
        t.key: _capacity(t.key) for t in TRIPS if t.final_status is TripStatus.SCHEDULED
    }
    booked: Counter[str] = Counter()
    for key, _, seats in BOOKINGS:
        booked[key] += seats
    assert [k for k, cap in capacity.items() if cap - booked[k] == 1] == ["lag-abj"]
