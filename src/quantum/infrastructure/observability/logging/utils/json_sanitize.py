from typing import Any

_MAX_STR_LEN = 10_000
_MAX_BYTES_PREVIEW = 64
_MAX_DEPTH = 8


# --- Internal Helpers
def _safe_str(obj: Any) -> str:
    """Cycle-safe stringification with truncation."""
    try:
        s = str(obj)
    except Exception:
        return "<unstringifiable>"
    return s[:_MAX_STR_LEN] + ("…" if len(s) > _MAX_STR_LEN else "")


def _sanitize_primitive(obj: Any) -> Any | None:
    """Return sanitized primitive, or None if not a primitive."""
    if obj is None or isinstance(obj, (bool, int, float)):
        return obj
    if isinstance(obj, str):
        return obj if len(obj) <= _MAX_STR_LEN else obj[:_MAX_STR_LEN] + "…"
    if isinstance(obj, bytes):
        preview = repr(obj[:_MAX_BYTES_PREVIEW])
        return preview + ("… (truncated)" if len(obj) > _MAX_BYTES_PREVIEW else "")
    return None  # means: not a primitive


def _sanitize_sequence(obj: Any, depth: int, visited: set[int]) -> Any | None:
    """Return sanitized sequence, or None if not a sequence."""
    if isinstance(obj, (list, tuple, set)):
        return [_sanitize(x, depth + 1, visited) for x in obj]
    return None


def _sanitize_mapping(obj: Any, depth: int, visited: set[int]) -> Any | None:
    """Return sanitized mapping, or None if not a mapping."""
    if isinstance(obj, dict):
        out: dict[str, Any] = {}
        for k, v in obj.items():
            out[_safe_str(k)] = _sanitize(v, depth + 1, visited)
        return out
    return None


def _sanitize(obj: Any, depth: int, visited: set[int]) -> Any:
    """Internal safe implementation. Never exposed."""

    # depth protection
    if depth > _MAX_DEPTH:
        return "<depth_limit_exceeded>"

    oid = id(obj)
    if oid in visited:
        return "<cycle_detected>"
    visited.add(oid)

    prim = _sanitize_primitive(obj)
    if prim is not None:
        return prim

    # Lists / tuples / sets → JSON-compatible list
    seq = _sanitize_sequence(obj, depth, visited)
    if seq is not None:
        return seq

    # Dicts
    mapping = _sanitize_mapping(obj, depth, visited)
    if mapping is not None:
        return mapping

    # Fallback
    return _safe_str(obj)


# --- Public API
def json_sanitize(obj: Any) -> Any:
    """Always safe, JSONable, depth-limited, deterministic."""
    try:
        return _sanitize(obj, depth=0, visited=set())
    except Exception:
        return "<unserializable>"
