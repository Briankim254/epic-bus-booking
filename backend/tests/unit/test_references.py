"""Booking references (PLAN §7.3)."""

import re

from app.domain.references import ALPHABET, generate_reference

PATTERN = re.compile(r"^BK-[0-9A-HJKMNP-TV-Z]{4}-[0-9A-HJKMNP-TV-Z]{4}$")


def test_format_and_alphabet() -> None:
    for _ in range(1000):
        ref = generate_reference()
        assert PATTERN.match(ref), ref
        assert len(ref) == 12  # fits bookings.reference varchar(12)


def test_alphabet_is_crockford_base32() -> None:
    assert len(ALPHABET) == 32
    assert not set("ILOU") & set(ALPHABET)


def test_no_duplicates_in_ten_thousand_draws() -> None:
    refs = {generate_reference() for _ in range(10_000)}
    assert len(refs) == 10_000
