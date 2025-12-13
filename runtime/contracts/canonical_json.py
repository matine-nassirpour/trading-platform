import json

from collections.abc import Mapping
from pathlib import Path
from types import MappingProxyType
from typing import Any


def _stable_object_fallback(obj: object) -> dict[str, Any]:
    """
    Stable, deterministic fallback for custom objects.

    Produces a minimal structure:
        {
            "__type__": "qualified.type.Name",
            "__fields__": { ... normalized fields ... } | None
        }

    • Never includes memory addresses.
    • Never relies on repr().
    • Ensures cross-run determinism for canonicalization.
    """

    typename = f"{obj.__class__.__module__}.{obj.__class__.__qualname__}"

    if hasattr(obj, "__dict__"):
        raw = vars(obj)
        # Raw dict → will be normalized later
        return {
            "__type__": typename,
            "__fields__": raw,
        }

    return {
        "__type__": typename,
        "__fields__": None,
    }


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

    # Sets → sorted list
    if isinstance(value, (set, frozenset)):
        return sorted(
            (_normalize(v, _seen=_seen) for v in value),
            key=lambda x: json.dumps(x, sort_keys=True),
        )

    # Mappings
    if isinstance(value, (MappingProxyType, Mapping)):
        items = [(str(k), _normalize(v, _seen=_seen)) for k, v in value.items()]
        items.sort(key=lambda kv: kv[0])
        return {k: v for k, v in items}

    # Path → string
    if isinstance(value, Path):
        return str(value)

    # Pydantic models
    if hasattr(value, "model_dump"):
        return _normalize(value.model_dump(), _seen=_seen)

    # Objects with __dict__
    if hasattr(value, "__dict__"):
        return _normalize(_stable_object_fallback(value), _seen=_seen)

    # Final fallback: stable type-based fallback
    return _stable_object_fallback(value)


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
