import json

from collections.abc import Mapping
from pathlib import Path
from types import MappingProxyType
from typing import Any


def _normalize(value: Any, *, _seen: set[int] | None = None) -> Any:
    """
    Convert recursively any object into a JSON-serializable structure.

    Handles:
        • Sequences / Sets / FrozenSets → list
        • MappingProxyType → dict
        • Mapping → dict
        • Path → str
        • Pydantic models → model_dump()
        • Arbitrary objects → vars() / str()
    """

    if _seen is None:
        _seen = set()

    obj_id = id(value)
    if obj_id in _seen:
        # Cycle detected → safe canonical marker
        return "<CYCLE>"

    # Track current object to detect cycles deeper in recursion.
    _seen.add(obj_id)

    # None / primitives
    if value is None or isinstance(value, (str, int, float, bool)):
        return value

    # Sequences / unordered sets → deterministic list
    if isinstance(value, (list, tuple)):
        return [_normalize(v, _seen=_seen) for v in value]

    if isinstance(value, (set, frozenset)):
        # Sort using stringified representation for deterministic ordering
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

    # Final fallback to stable string
    return str(value)


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
