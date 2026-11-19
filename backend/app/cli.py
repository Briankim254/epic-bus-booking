"""Operational commands: python -m app.cli {seed,reconcile,purge-idempotency}."""

import argparse
import sys

from app.core.db import SessionLocal
from app.core.logging import configure_logging


def seed(args: argparse.Namespace) -> int:
    from app.seed import seed as run_seed

    with SessionLocal() as session:
        run_seed(session, reset=args.reset)
    print("seed: ok" + (" (reset)" if args.reset else ""))
    return 0


def reconcile(_: argparse.Namespace) -> int:
    from app.services.reconciliation import find_drift

    with SessionLocal() as session:
        drift = find_drift(session)
    for d in drift:
        print(f"DRIFT trip={d.trip_id} counter={d.counter} actual={d.actual}")
    print(f"reconcile: {len(drift)} drifted trip(s)")
    return 1 if drift else 0


def purge_idempotency(args: argparse.Namespace) -> int:
    from datetime import timedelta

    from app.core.clock import utcnow
    from app.repositories.idempotency import IdempotencyRepository

    cutoff = utcnow() - timedelta(hours=args.hours)
    with SessionLocal() as session:
        deleted = IdempotencyRepository(session).purge(cutoff)
        session.commit()
    print(f"purge-idempotency: deleted {deleted} key(s) older than {args.hours}h")
    return 0


def main(argv: list[str] | None = None) -> int:
    configure_logging()
    parser = argparse.ArgumentParser(prog="python -m app.cli")
    sub = parser.add_subparsers(dest="command", required=True)
    p_seed = sub.add_parser(
        "seed", help="upsert reference data; add trips and bookings if empty"
    )
    p_seed.add_argument(
        "--reset", action="store_true", help="wipe trips and bookings first"
    )
    p_seed.set_defaults(func=seed)
    sub.add_parser(
        "reconcile", help="compare seat counters with bookings"
    ).set_defaults(func=reconcile)
    p_purge = sub.add_parser(
        "purge-idempotency", help="delete Idempotency-Key records past their TTL"
    )
    p_purge.add_argument("--hours", type=int, default=24, help="TTL (default 24)")
    p_purge.set_defaults(func=purge_idempotency)
    args = parser.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    sys.exit(main())
