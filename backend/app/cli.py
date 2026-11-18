"""Operational commands: python -m app.cli {seed,reconcile,purge-idempotency}."""

import argparse
import sys


def seed() -> int:
    print("seed: nothing to seed yet")
    return 0


def reconcile() -> int:
    print("reconcile: no trips table yet")
    return 0


def purge_idempotency() -> int:
    print("purge-idempotency: no idempotency table yet")
    return 0


COMMANDS = {
    "seed": seed,
    "reconcile": reconcile,
    "purge-idempotency": purge_idempotency,
}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m app.cli")
    parser.add_argument("command", choices=sorted(COMMANDS))
    args = parser.parse_args(argv)
    return COMMANDS[args.command]()


if __name__ == "__main__":
    sys.exit(main())
