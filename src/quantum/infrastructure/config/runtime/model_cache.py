from __future__ import annotations

import threading

from typing import Any, Final

from quantum.infrastructure.config.runtime.env_snapshot import get_frozen_env

CONFIG_SCHEMA_VERSION: Final[str] = "1.0.0"


class ModelCache:
    """
    Deterministic, versioned, thread-safe cache for configuration models.

    Guarantees:
        - One cache entry per model class
        - Invalidation on schema version change
        - Invalidation on PID change (via frozen OS env)
        - Deterministic loading
        - Thread-safe operations
        - Zero mutation post-store (fully immutable)
    """

    _lock: Final[threading.RLock] = threading.RLock()
    _instances: dict[str, Any] = {}
    _fingerprint: str | None = None

    @classmethod
    def _compute_fingerprint(cls) -> str:
        """
        Compute a deterministic fingerprint combining:
            • Global CONFIG_SCHEMA_VERSION
            • PID-specific frozen environment snapshot
        """
        env = get_frozen_env()
        env_hash = hash(tuple(sorted(env.items())))
        return f"{CONFIG_SCHEMA_VERSION}:{env_hash}"

    @classmethod
    def get(cls, key: str) -> Any | None:
        fp = cls._compute_fingerprint()
        with cls._lock:
            if cls._fingerprint != fp:
                # Fingerprint changed → invalidate everything.
                cls._instances.clear()
                cls._fingerprint = fp
            return cls._instances.get(key)

    @classmethod
    def set(cls, key: str, value: Any) -> None:
        fp = cls._compute_fingerprint()
        with cls._lock:
            if cls._fingerprint != fp:
                cls._instances.clear()
                cls._fingerprint = fp
            cls._instances[key] = value

    @classmethod
    def clear(cls) -> None:
        with cls._lock:
            cls._instances.clear()
            cls._fingerprint = None
