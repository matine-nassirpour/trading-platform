import json

from collections.abc import Mapping
from pathlib import Path
from types import MappingProxyType
from typing import Any


def _normalize(value: Any, *, _seen: set[int] | None = None) -> Any:
    """
    Normalize any Python object into a fully JSON-serializable structure.

    Notes
    -----
    • Cycle detection uses a 'visited set':
        - A repeated reference is represented as the string "<CYCLE>".
        - This covers both true cycles and shared-object references.
        - This is intentional and documented for diagnostics.

    • No attempt is made to preserve object identity or reference graphs.

    • This function MUST remain side-effect-free and deterministic.
    """

    if _seen is None:
        _seen = set()

    # None / primitives
    if value is None or isinstance(value, (str, int, float, bool)):
        return value

    obj_id = id(value)
    if obj_id in _seen:
        # Cycle detected → safe canonical marker
        return "<CYCLE>"

    # Track current object to detect cycles deeper in recursion.
    _seen.add(obj_id)

    # Sequences / unordered sets → deterministic list
    if isinstance(value, (list, tuple)):
        return [_normalize(v, _seen=_seen) for v in value]

    # Sets (sorted deterministically)
    if isinstance(value, (set, frozenset)):
        return sorted(
            (_normalize(v, _seen=_seen) for v in value),
            key=lambda x: json.dumps(x, sort_keys=True),
        )

    # MappingProxyType and general Mapping
    if isinstance(value, MappingProxyType) or isinstance(value, Mapping):
        # Normalize keys → canonical string keys
        normalized_items = [
            (str(k), _normalize(v, _seen=_seen)) for k, v in value.items()
        ]
        # Ensure deterministic ordering
        normalized_items.sort(key=lambda kv: kv[0])
        return {k: v for k, v in normalized_items}

    # Path → string
    if isinstance(value, Path):
        return str(value)

    # Pydantic models
    if hasattr(value, "model_dump"):
        return _normalize(value.model_dump(), _seen=_seen)

    # Objects with __dict__
    if hasattr(value, "__dict__"):
        return _normalize(vars(value), _seen=_seen)

    # Final fallback to stable repr
    return repr(value)


def canonical_json(data: object) -> str:
    """
    Produce a canonical JSON representation:
        • All objects normalized to JSON-safe structures
        • Sorted keys (deterministic ordering)
        • Compact separators
        • UTF-8 safe
    """

    normalized = _normalize(data)
    return json.dumps(
        normalized,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    )
