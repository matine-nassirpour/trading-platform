from __future__ import annotations

import os
import threading

from collections.abc import Mapping
from types import MappingProxyType
from typing import Final

from quantum.infrastructure.config.environment.core.normalization import (
    normalize_env_keys,
)


class FrozenEnvironment:
    """
    Industry-grade, PID-stable, immutable snapshot of OS environment variables.

    Guarantees:
        • Captured once per process
        • Internally immutable (MappingProxyType)
        • Thread-safe initialization
        • Deterministic for process lifetime
        • Prevents accidental reliance on mutated os.environ
    """

    _lock: Final[threading.RLock] = threading.RLock()
    _snapshot: Mapping[str, str] | None = None
    _pid: int | None = None

    @classmethod
    def get(cls) -> Mapping[str, str]:
        with cls._lock:
            pid = os.getpid()

            if cls._pid != pid or cls._snapshot is None:
                normalized = normalize_env_keys(os.environ)
                cls._snapshot = MappingProxyType(dict(normalized))
                cls._pid = pid

            return cls._snapshot


def get_frozen_env() -> Mapping[str, str]:
    """Return the immutable snapshot of the OS environment."""
    return FrozenEnvironment.get()
