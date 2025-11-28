from __future__ import annotations

import hashlib
import json
import threading

from typing import Final

from quantum.infrastructure.config.runtime.fsm.model import (
    ConfigFSMState,
    ConfigLifecycleStatus,
)


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
            "env": dict(state.env or {}),
            "settings": {k: dict(v) for k, v in dict(state.settings or {}).items()},
            "metadata": dict(state.metadata or {}),
        }

        canonical = _canonical_json(normalized)
        digest = _hash_sha256(canonical)

        return f"SHA256:{digest}"

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
            if cls._fingerprint == fp:
                return  # Already cached, nothing to do

            cls._state = state
            cls._fingerprint = fp

    @classmethod
    def clear(cls) -> None:
        with cls._lock:
            cls._state = None
            cls._fingerprint = None
