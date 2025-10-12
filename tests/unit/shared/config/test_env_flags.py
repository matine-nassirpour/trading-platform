from __future__ import annotations

from quantum.shared.config.env_flags import get_bool


def test_get_bool_truthy_and_falsy_variants():
    """
    Given a dict of environment-like values
    When calling get_bool(key, default, env=...)
    Then canonical truthy/falsy variants are recognized,
         whitespace/casing are handled, and ambiguous values fall back to default.
    """
    env = {
        "A": "1",
        "B": "true",
        "C": "Yes",
        "D": "ON",
        "E": "0",
        "F": "false",
        "G": "no",
        "H": "off",
        "I": "   TrUe   ",
        "J": "   ",
        "K": "weird",
        "L": "",
    }
    assert get_bool("A", env=env) is True
    assert get_bool("B", env=env) is True
    assert get_bool("C", env=env) is True
    assert get_bool("D", env=env) is True

    assert get_bool("E", env=env) is False
    assert get_bool("F", env=env) is False
    assert get_bool("G", env=env) is False
    assert get_bool("H", env=env) is False

    # Trimming + casefold
    assert get_bool("I", env=env) is True

    # Empty/absent → default
    assert get_bool("J", default=False, env=env) is False
    assert get_bool("L", default=True, env=env) is True

    # Ambiguous → default
    assert get_bool("K", default=True, env=env) is True
    assert get_bool("K", default=False, env=env) is False
