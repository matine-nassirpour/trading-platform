from __future__ import annotations

from typing import Any


def safe_expose(value: Any) -> Any:
    """
    Recursively sanitize a value for external exposure.

    Responsibilities:
    - Ensure only JSON-safe primitive structures are exposed
    - Strip runtime-only object references
    - Preserve structure deterministically

    Guarantees:
    - Deterministic
    - Side-effect free
    - Never raises
    """

    if isinstance(value, dict):
        return {k: safe_expose(v) for k, v in value.items()}

    if isinstance(value, (list, tuple)):
        return [safe_expose(v) for v in value]

    return value
