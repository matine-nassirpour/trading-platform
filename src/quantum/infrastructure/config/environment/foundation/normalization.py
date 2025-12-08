from __future__ import annotations

import unicodedata

from collections.abc import Mapping


class EnvKeyNormalizationError(ValueError):
    """Raised when key normalization encounters unsafe collisions."""


def normalize_env_keys(env: Mapping[str, str]) -> dict[str, str]:
    """
    Normalize environment keys to lowercase NFKC-safe identifiers.

    Guarantees:
        • Pure transformation
        • Keys become strictly lowercase
        • Unicode NFKC normalization
        • Detects and forbids key collisions (e.g. DB_PASS vs db_pass)
        • Deterministic final mapping
    """

    normalized: dict[str, str] = {}

    for raw_key, raw_value in env.items():
        if raw_value is None:
            continue  # dotenv may produce None for unset keys

        # 1. Normalize Unicode
        key = unicodedata.normalize("NFKC", str(raw_key))

        # 2. Enforce lowercase canonical form
        key = key.lower()

        # 3. Collision detection
        if key in normalized:
            raise EnvKeyNormalizationError(
                f"Key collision detected during environment normalization: "
                f"'{raw_key}' conflicts with existing normalized key '{key}'. "
                "Ensure environment variable names are unique in a "
                "case-insensitive manner."
            )

        normalized[key] = raw_value

    return normalized
