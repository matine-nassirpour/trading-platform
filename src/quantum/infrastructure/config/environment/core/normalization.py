from __future__ import annotations

import re
import unicodedata

from collections.abc import Mapping

_VALID_KEY = re.compile(r"^[a-z0-9_]+$")


class EnvKeyNormalizationError(ValueError):
    """Raised when key normalization encounters unsafe collisions or invalid characters."""


def normalize_env_keys(env: Mapping[str, str | None]) -> dict[str, str]:
    """
    Normalize and validate environment keys.

    Guarantees:
        • Unicode NFKC normalization
        • Lowercase
        • No internal spaces
        • Pattern ^[a-z0-9_]+$
        • No empty keys
        • Collision detection
    """

    normalized: dict[str, str] = {}

    for raw_key, raw_value in env.items():
        if raw_value is None:
            continue  # dotenv may produce None for unset keys

        key = unicodedata.normalize("NFKC", str(raw_key)).strip()

        if not key:
            raise EnvKeyNormalizationError(
                f"Environment variable with empty key detected (raw='{raw_key}')."
            )

        if " " in key:
            raise EnvKeyNormalizationError(
                f"Invalid environment key '{raw_key}': spaces are forbidden."
            )

        key = key.lower()

        if not _VALID_KEY.fullmatch(key):
            raise EnvKeyNormalizationError(
                f"Invalid characters in environment key '{raw_key}'. "
                f"Allowed pattern: {_VALID_KEY.pattern}"
            )

        if key in normalized:
            raise EnvKeyNormalizationError(
                f"Key collision during normalization: '{raw_key}' → '{key}'."
            )

        normalized[key] = raw_value

    return normalized
