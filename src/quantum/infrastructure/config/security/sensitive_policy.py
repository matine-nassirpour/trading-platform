from __future__ import annotations

from typing import Final

GLOBAL_SENSITIVE_PATTERNS: Final[frozenset[str]] = frozenset(
    {
        "password",
        "secret",
        "token",
        "apikey",
        "api_key",
        "credential",
        "headers",
    }
)


def is_sensitive_key(key: str) -> bool:
    """
    Global defensive rule to detect sensitive keys regardless of model declarations.

    - Case-insensitive
    - Pattern-based
    - Matches any substring containing patterns listed above

    This ensures future fields added by mistake (e.g. new API keys)
    are automatically masked without requiring model updates.
    """
    k = key.lower()
    return any(p in k for p in GLOBAL_SENSITIVE_PATTERNS)
