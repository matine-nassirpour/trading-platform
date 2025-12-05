import json

from collections.abc import Mapping
from pathlib import Path
from types import MappingProxyType


def _normalize(value):
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

    # None / primitives
    if value is None or isinstance(value, (str, int, float, bool)):
        return value

    # Sequences / sets → list
    if isinstance(value, (list, tuple, set, frozenset)):
        return [_normalize(v) for v in value]

    # MappingProxyType (immutable mapping wrapper)
    if isinstance(value, MappingProxyType):
        return {k: _normalize(v) for k, v in value.items()}

    # General mappings
    if isinstance(value, Mapping):
        return {str(k): _normalize(v) for k, v in value.items()}

    # Path → str
    if isinstance(value, Path):
        return str(value)

    # Pydantic models
    if hasattr(value, "model_dump"):
        return _normalize(value.model_dump())

    # Generic objects with __dict__
    if hasattr(value, "__dict__"):
        return _normalize(vars(value))

    # Fallback safe string
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
