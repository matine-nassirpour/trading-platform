from __future__ import annotations

import os
from collections.abc import Mapping

_TRUE = {"1", "true", "t", "yes", "y", "on"}
_FALSE = {"0", "false", "f", "no", "n", "off"}


def get_bool(
    name: str, default: bool = False, *, env: Mapping[str, str] | None = None
) -> bool:
    """
    Parses an environment boolean in a robust and consistent manner.

    Target convention (doc): 'true' / 'false' (case-insensitive).
    Backwards compatibility: also accepts 1/0, yes/no, on/off.

    - If the variable is absent → default
    - If the value is empty → default
    - If ambiguous/invalid → default (fail-safe)
    """
    src = env if env is not None else os.environ
    raw = src.get(name)
    if raw is None:
        return default
    v = raw.strip().lower()
    if not v:
        return default
    if v in _TRUE:
        return True
    if v in _FALSE:
        return False
    return default
