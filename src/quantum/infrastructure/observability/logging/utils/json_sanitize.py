from __future__ import annotations

from typing import Any

_MAX_STR_LEN = 10_000
_MAX_BYTES_PREVIEW = 64


# ╭────────────────────────────────────────────────────────────────────────────╮
# │ Internal Helpers                                                           │
# ╰────────────────────────────────────────────────────────────────────────────╯
def _sanitize(obj: Any) -> Any:
    """Internal safe implementation. Never exposed."""
    # Fast paths for simple primitives
    if obj is None or isinstance(obj, (bool, int, float)):
        return obj

    if isinstance(obj, str):
        return obj if len(obj) <= _MAX_STR_LEN else obj[:_MAX_STR_LEN] + "…"

    if isinstance(obj, bytes):
        preview = repr(obj[:_MAX_BYTES_PREVIEW])
        return preview + ("… (truncated)" if len(obj) > _MAX_BYTES_PREVIEW else "")

    if isinstance(obj, (list, tuple, set)):
        return [_sanitize(x) for x in obj]

    if isinstance(obj, dict):
        return {str(k): _sanitize(v) for k, v in obj.items()}

    # Last resort: stable stringification
    s = str(obj)
    return s[:_MAX_STR_LEN] + ("…" if len(s) > _MAX_STR_LEN else "")


# ╭────────────────────────────────────────────────────────────────────────────╮
# │ Public API                                                                 │
# ╰────────────────────────────────────────────────────────────────────────────╯
def json_sanitize(obj: Any) -> Any:
    """
    Convert arbitrary Python objects into JSON-safe, deterministic structures.

    Goals:
    - Ensure json.dumps() NEVER fails due to unserializable types.
    - Prevent uncontrolled memory explosion by truncating large strings/bytes.
    - Recursively sanitize lists, sets, dicts, and custom objects.
    - Preserve readability and deterministic output for logging pipelines.

    Returns:
        Sanitized object (primitive or structure fully compatible with JSON).
    """
    try:
        return _sanitize(obj)
    except Exception:
        # Absolute fail-safe: fallback to safe stringification of the object.
        try:
            s = str(obj)
            return s[:_MAX_STR_LEN] + ("…" if len(s) > _MAX_STR_LEN else "")
        except Exception:
            return "<unserializable>"
