from __future__ import annotations

import threading

from typing import Final

from quantum.infrastructure.config.runtime.fsm_model import (
    ConfigFSMState,
    ConfigLifecycleStatus,
)


class ReadyStateCache:
    """
    Cache storing the *entire* FSM READY state.

    Guarantees:
        • Immutable storage
        • Thread-safe
        • Invalidated when fingerprint changes
        • Canonically tied to the final deterministic READY state
    """

    _lock: Final[threading.RLock] = threading.RLock()
    _state: ConfigFSMState | None = None
    _fingerprint: str | None = None

    @staticmethod
    def _compute_fingerprint(state: ConfigFSMState) -> str:
        """
        Compute canonical fingerprint based on the full READY state.
        Includes:
            • Schema version (implicit via settings)
            • Environment dict normalized
            • Settings dict normalized
            • Metadata dict normalized
        """
        if state.status is not ConfigLifecycleStatus.READY:
            raise ValueError("Fingerprint can only be computed for READY states.")

        env_items = tuple(sorted(state.env.items())) if state.env else ()
        settings_items = tuple(
            sorted(
                (k, tuple(sorted(v.items()))) for k, v in (state.settings or {}).items()
            )
        )
        meta_items = tuple(sorted(state.metadata.items())) if state.metadata else ()

        return f"FP:{hash(env_items)}:{hash(settings_items)}:{hash(meta_items)}"

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
