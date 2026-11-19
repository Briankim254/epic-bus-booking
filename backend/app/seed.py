"""Seed data from the brief: 6 towns in 4 zones, 4 buses, ~10 trips, ~15 bookings.

Run with `python -m app.cli seed` (prestart does this on every start).

- Reference data (zones, towns, fares) is upserted every time, so it is safe to re-run.
- Buses are inserted by plate number if missing, but never overwritten, so an operator's
  edits survive a restart. `--reset` restores them to the values below.
- Every trip is assigned a bus and copies that bus's capacity from the database (A9).
- Trips and bookings are inserted only when `trips` is empty. Pass `--reset` to wipe and
  re-create them.
- Departure times are relative to now, so there are always future trips to search.
- Bookings are written while their trip is still `scheduled` and then trips are advanced
  through the state machine, so departed/arrived trips have bookings and every counter is
  consistent. The run ends with a reconciliation check and fails loudly on any drift.
"""

import logging
from dataclasses import dataclass
from datetime import UTC, datetime, time, timedelta
from zoneinfo import ZoneInfo

from sqlalchemy import func, select, text, update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from app.domain.references import generate_reference
from app.domain.trip_status import TripStatus, assert_transition, path_to
from app.models import Booking, Bus, Town, Trip, Zone, ZoneFare
from app.services.reconciliation import find_drift

logger = logging.getLogger("app.seed")
LAGOS = ZoneInfo("Africa/Lagos")

ZONES = {1: "Lagos region", 2: "South-East", 3: "Middle Belt", 4: "North"}

# id -> (name, zone). Ids are fixed so README examples stay stable.
TOWNS = {
    1: ("Lagos", 1),
    2: ("Ibadan", 1),
    3: ("Enugu", 2),
    4: ("Onitsha", 2),
    5: ("Abuja", 3),
    6: ("Kano", 4),
}

# (low zone, high zone) -> fare in US cents, from the brief's fare table.
FARES = {
    (1, 1): 800,
    (1, 2): 1800,
    (1, 3): 2500,
    (1, 4): 3500,
    (2, 2): 1000,
    (2, 3): 1800,
    (2, 4): 2800,
    (3, 3): 800,
    (3, 4): 2200,
    (4, 4): 800,
}

# plate -> (name, capacity). Dummy plates; two 44-seat and two 40-seat coaches.
BUSES = {
    "TEST-001": ("Coach 01", 44),
    "TEST-002": ("Coach 02", 44),
    "TEST-003": ("Coach 03", 40),
    "TEST-004": ("Coach 04", 40),
}


@dataclass(frozen=True)
class TripSeed:
    key: str
    origin: str
    destination: str
    day_offset: int  # Lagos calendar days from today
    local_time: time  # Lagos departure time
    bus: str  # plate number; the trip copies this bus's capacity
    final_status: TripStatus = TripStatus.SCHEDULED


# No bus runs two trips on the same day. Overlaps aren't enforced (see PLAN, trade-offs).
TRIPS = [
    TripSeed("lag-abj", "Lagos", "Abuja", 1, time(8, 30), "TEST-001"),  # 1 seat left
    TripSeed("abj-lag", "Abuja", "Lagos", 1, time(14, 0), "TEST-002"),
    TripSeed("lag-iba", "Lagos", "Ibadan", 1, time(7, 0), "TEST-003"),
    TripSeed("enu-oni", "Enugu", "Onitsha", 1, time(9, 0), "TEST-004"),
    TripSeed("lag-enu", "Lagos", "Enugu", 2, time(6, 30), "TEST-001"),
    TripSeed("kan-abj", "Kano", "Abuja", 2, time(10, 0), "TEST-003"),
    TripSeed("iba-kan", "Ibadan", "Kano", 3, time(5, 45), "TEST-002"),
    TripSeed("oni-lag", "Onitsha", "Lagos", 3, time(20, 0), "TEST-004"),
    TripSeed(
        "lag-kan", "Lagos", "Kano", 0, time(0, 0), "TEST-002", TripStatus.DEPARTED
    ),
    TripSeed(
        "abj-enu", "Abuja", "Enugu", -1, time(9, 0), "TEST-003", TripStatus.ARRIVED
    ),
]

# (trip key, passenger name, seats). 15 bookings; names include diacritics on purpose.
BOOKINGS = [
    ("lag-abj", "Adebayo Ogunleye", 10),
    ("lag-abj", "Chiamaka Eze", 10),
    ("lag-abj", "Ọláyíwọlá Adéyẹmí", 10),
    ("lag-abj", "Musa Ibrahim", 10),
    ("lag-abj", "Ngozi Okafor", 3),
    ("lag-iba", "Tunde Bakare", 2),
    ("lag-iba", "Funmilayo Adeyemi", 1),
    ("abj-lag", "Halima Bello", 4),
    ("lag-enu", "Chukwuemeka Obi", 2),
    ("lag-enu", "Aisha Danjuma", 1),
    ("kan-abj", "Sani Abdullahi", 3),
    ("lag-kan", "Emeka Nwosu", 2),
    ("lag-kan", "Zainab Yusuf", 5),
    ("abj-enu", "Ifeoma O'Neil-Okeke", 2),
    ("abj-enu", "Yakubu Garba", 6),
]


def seed(session: Session, *, reset: bool = False, now: datetime | None = None) -> None:
    now = now or datetime.now(UTC)
    _upsert_reference_data(session)
    _insert_buses(session, overwrite=reset)

    if reset:
        session.execute(text("TRUNCATE bookings, trips RESTART IDENTITY CASCADE"))
    if session.scalar(select(func.count()).select_from(Trip)):
        logger.info("seed.skipped", extra={"reason": "trips already present"})
        session.commit()
        _check_drift(session)
        return

    trips = _insert_trips(session, now)
    for key, name, seats in BOOKINGS:
        _book(session, trips[key], name, seats)
    for spec in TRIPS:
        _advance(session, trips[spec.key], spec.final_status)

    session.commit()
    _check_drift(session)
    logger.info("seed.done", extra={"trips": len(TRIPS), "bookings": len(BOOKINGS)})


def _upsert_reference_data(session: Session) -> None:
    zones = insert(Zone).values([{"id": i, "name": n} for i, n in ZONES.items()])
    session.execute(
        zones.on_conflict_do_update(
            index_elements=["id"], set_={"name": zones.excluded.name}
        )
    )

    towns = insert(Town).values(
        [{"id": i, "name": n, "zone_id": z} for i, (n, z) in TOWNS.items()]
    )
    session.execute(
        towns.on_conflict_do_update(
            index_elements=["id"],
            set_={"name": towns.excluded.name, "zone_id": towns.excluded.zone_id},
        )
    )

    fares = insert(ZoneFare).values(
        [
            {"zone_a_id": a, "zone_b_id": b, "fare_cents": c}
            for (a, b), c in FARES.items()
        ]
    )
    session.execute(
        fares.on_conflict_do_update(
            index_elements=["zone_a_id", "zone_b_id"],
            set_={"fare_cents": fares.excluded.fare_cents},
        )
    )


def _insert_buses(session: Session, *, overwrite: bool) -> None:
    buses = insert(Bus).values(
        [
            {"plate_number": p, "name": n, "capacity": c, "active": True}
            for p, (n, c) in BUSES.items()
        ]
    )
    if overwrite:
        stmt = buses.on_conflict_do_update(
            index_elements=["plate_number"],
            set_={
                "name": buses.excluded.name,
                "capacity": buses.excluded.capacity,
                "active": buses.excluded.active,
                "updated_at": func.now(),
            },
        )
    else:
        stmt = buses.on_conflict_do_nothing(index_elements=["plate_number"])
    session.execute(stmt)


def _departure(now: datetime, spec: TripSeed) -> datetime:
    if spec.final_status is TripStatus.DEPARTED:
        return now - timedelta(hours=2)  # on the road right now
    today = now.astimezone(LAGOS).date()
    local = datetime.combine(
        today + timedelta(days=spec.day_offset), spec.local_time, LAGOS
    )
    return local.astimezone(UTC)


def _insert_trips(session: Session, now: datetime) -> dict[str, Trip]:
    town_ids = {name: i for i, (name, _) in TOWNS.items()}
    buses = {b.plate_number: b for b in session.scalars(select(Bus))}
    trips: dict[str, Trip] = {}
    for spec in TRIPS:
        bus = buses[spec.bus]
        trip = Trip(
            origin_town_id=town_ids[spec.origin],
            destination_town_id=town_ids[spec.destination],
            bus_id=bus.id,
            departs_at=_departure(now, spec),
            capacity=bus.capacity,  # copied on assignment (A9)
            status=TripStatus.SCHEDULED,
        )
        session.add(trip)
        trips[spec.key] = trip
    session.flush()
    return trips


def _fare_cents(session: Session, trip: Trip) -> int:
    """Read the fare from zone_fares (the source of truth), normalising the zone pair."""
    oz, dz = TOWNS[trip.origin_town_id][1], TOWNS[trip.destination_town_id][1]
    fare = session.scalar(
        select(ZoneFare.fare_cents).where(
            ZoneFare.zone_a_id == min(oz, dz), ZoneFare.zone_b_id == max(oz, dz)
        )
    )
    if fare is None:
        raise RuntimeError(f"no fare configured for zones {oz} and {dz}")
    return fare


def _book(session: Session, trip: Trip, name: str, seats: int) -> None:
    # Same atomic, conditional counter update the booking service uses. The departure-time
    # check is left out so trips that are already in the past can carry historic bookings.
    # TODO(booking service): call BookingService with an injected clock instead.
    updated = session.execute(
        update(Trip)
        .where(
            Trip.id == trip.id,
            Trip.status == TripStatus.SCHEDULED,
            Trip.seats_booked + seats <= Trip.capacity,
        )
        .values(seats_booked=Trip.seats_booked + seats)
        .returning(Trip.id)
    ).first()
    if updated is None:
        raise RuntimeError(f"seed booking rejected for trip {trip.id}")
    fare = _fare_cents(session, trip)
    session.add(
        Booking(
            reference=generate_reference(),
            trip_id=trip.id,
            passenger_name=name,
            seats=seats,
            fare_cents_per_seat=fare,
            total_cents=fare * seats,
        )
    )
    session.flush()


def _advance(session: Session, trip: Trip, target: TripStatus) -> None:
    current = TripStatus.SCHEDULED
    for step in path_to(target) if target is not TripStatus.SCHEDULED else []:
        assert_transition(current, step)
        session.execute(
            update(Trip)
            .where(Trip.id == trip.id, Trip.status == current)
            .values(status=step)
        )
        current = step


def _check_drift(session: Session) -> None:
    drift = find_drift(session)
    if drift:
        raise RuntimeError(f"seat counter drift after seeding: {drift}")
