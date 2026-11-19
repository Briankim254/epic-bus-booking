"""Booking references: BK-XXXX-XXXX from a CSPRNG over Crockford base32 (no I, L, O, U)."""

import secrets

ALPHABET = "0123456789ABCDEFGHJKMNPQRSTVWXYZ"


def generate_reference() -> str:
    chars = "".join(secrets.choice(ALPHABET) for _ in range(8))
    return f"BK-{chars[:4]}-{chars[4:]}"
