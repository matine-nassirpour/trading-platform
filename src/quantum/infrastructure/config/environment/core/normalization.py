from __future__ import annotations

import unicodedata

from collections.abc import Mapping


class EnvKeyNormalizationError(ValueError):
    """Raised when key normalization encounters unsafe collisions or invalid characters."""


def normalize_env_keys(env: Mapping[str, str | None]) -> dict[str, str]:
    """
    Normalize environment keys to strict lowercase NFKC-safe identifiers.

    Guarantees:
        • Pure transformation
        • Keys become strictly lowercase
        • Unicode NFKC normalization
        • Strips surrounding whitespace
        • Rejects keys containing internal spaces
        • Detects and forbids key collisions
        • Deterministic final mapping
    """

    normalized: dict[str, str] = {}

    for raw_key, raw_value in env.items():
        if raw_value is None:
            continue  # dotenv may produce None for unset keys

        key = unicodedata.normalize("NFKC", str(raw_key)).strip()

        if " " in key:
            raise EnvKeyNormalizationError(
                f"Invalid environment variable key '{raw_key}': "
                "spaces are not allowed in normalized keys."
            )

        key = key.lower()

        if key in normalized:
            raise EnvKeyNormalizationError(
                f"Key collision detected during environment normalization: "
                f"'{raw_key}' conflicts with existing normalized key '{key}'."
            )

        normalized[key] = raw_value

    return normalized
