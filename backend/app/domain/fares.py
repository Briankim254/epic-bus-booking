"""Fare rules. Pure: no imports from the rest of the app except domain errors.

The fare depends only on the two towns' zones. The table stores one row per unordered zone
pair, keyed (low zone, high zone), so symmetry holds by construction.
"""

from collections.abc import Mapping
from dataclasses import dataclass

from app.domain.errors import FareNotConfigured, SameTownError

FareTable = Mapping[tuple[int, int], int]  # (low zone, high zone) -> US cents


@dataclass(frozen=True)
class TownRef:
    id: int
    zone_id: int


def fare_for_zones(origin_zone: int, destination_zone: int, table: FareTable) -> int:
    key = (min(origin_zone, destination_zone), max(origin_zone, destination_zone))
    try:
        return table[key]
    except KeyError:
        raise FareNotConfigured(
            f"No fare between zones {key[0]} and {key[1]}."
        ) from None


def quote(origin: TownRef, destination: TownRef, table: FareTable) -> int:
    """Per-seat fare in US cents for a journey between two different towns (A2, A4)."""
    if origin.id == destination.id:
        raise SameTownError
    return fare_for_zones(origin.zone_id, destination.zone_id, table)
