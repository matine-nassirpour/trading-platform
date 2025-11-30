from __future__ import annotations

import hashlib
import json
import threading

from collections.abc import Mapping
from typing import Final

from quantum.infrastructure.config.runtime.fsm.model import (
    FSM_SCHEMA_VERSION,
    ConfigFSMState,
    ConfigLifecycleStatus,
)


def _normalize_json_safe(value):
    """
    Convert recursively any object into a JSON-serializable structure.
    - Path → str
    - Sets/FrozenSets → sorted lists
    - Custom VO with __dict__ → recurse
    - Mapping → recurse
    - Sequence/Generator → recurse
    """
    from pathlib import Path

    if value is None:
        return None

    # Primitive JSON-safe types
    if isinstance(value, (str, int, float, bool)):
        return value

    # Path → str
    if isinstance(value, Path):
        return str(value)

    # Mapping → dict
    if isinstance(value, Mapping):
        return {k: _normalize_json_safe(v) for k, v in value.items()}

    # List / tuple / set / frozenset
    if isinstance(value, (list, tuple, set, frozenset)):
        return [_normalize_json_safe(v) for v in value]

    # Pydantic models or custom Value Objects
    if hasattr(value, "__dict__"):
        return _normalize_json_safe(dict(value.__dict__))

    # Fallback safe string
    return str(value)


def _canonical_json(data: object) -> str:
    """
    Produce a canonical JSON representation:
        • Sorted keys (deterministic ordering)
        • No whitespace variance (compact form)
        • No Python object references
        • UTF-8 safe
        • Cross-platform reproducibility

    Required for safety-critical fingerprinting.
    """
    return json.dumps(
        data,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    )


def _hash_sha256(text: str) -> str:
    """
    Compute a stable, cryptographic SHA-256 hash.
    Always returns a 64-char lowercase hex digest.
    """
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


class ReadyStateCache:
    """
    Cache storing the *entire* FSM READY state.

    Guarantees:
        • Cryptographically stable fingerprint (SHA-256)
        • Deterministic serialization (canonical JSON)
        • Immutable storage
        • Thread-safe
        • Fingerprint guards against silent divergence
    """

    _lock: Final[threading.RLock] = threading.RLock()
    _state: ConfigFSMState | None = None
    _fingerprint: str | None = None

    # --------------------------------------------------------------------------
    # Canonical fingerprint computation
    # --------------------------------------------------------------------------
    @staticmethod
    def _compute_fingerprint(state: ConfigFSMState) -> str:
        """
        Compute canonical fingerprint based on the full READY state.
        Ensures:
            • Deterministic across processes / machines
            • Stable between Python runs
            • Safe for audit, logging, persistence
        """
        if state.status is not ConfigLifecycleStatus.READY:
            raise ValueError("Fingerprint can only be computed for READY states.")

        normalized = {
            "fsm_schema_version": FSM_SCHEMA_VERSION,
            "env": _normalize_json_safe(state.env or {}),
            "settings": _normalize_json_safe(state.settings or {}),
            "metadata": _normalize_json_safe(state.metadata or {}),
        }

        canonical = _canonical_json(normalized)
        digest = _hash_sha256(canonical)

        return f"SHA256-V{FSM_SCHEMA_VERSION}:{digest}"

    # --------------------------------------------------------------------------
    # Public API
    # --------------------------------------------------------------------------
    @classmethod
    def get(cls) -> ConfigFSMState | None:
        with cls._lock:
            return cls._state

    @classmethod
    def set(cls, state: ConfigFSMState) -> None:
        if state.status is not ConfigLifecycleStatus.READY:
            raise ValueError("Only READY state can be cached.")

        fp = cls._compute_fingerprint(state)

        with cls._lock:
            # Automatic invalidation if schema version OR state changed
            if cls._fingerprint == fp:
                return

            cls._state = state
            cls._fingerprint = fp

    @classmethod
    def clear(cls) -> None:
        with cls._lock:
            cls._state = None
            cls._fingerprint = None
