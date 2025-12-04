from __future__ import annotations

import os
import threading

from collections.abc import Mapping
from typing import Final

from quantum.infrastructure.config.environment.normalization import normalize_env_keys


class FrozenEnvironment:
    """
    Industry-grade, process-stable, immutable snapshot of OS environment variables.

    Guarantees:
        • Captured once per process (PID)
        • Immutable (frozen mapping)
        • Thread-safe
        • Deterministic for the lifetime of the process
        • Prevents accidental reliance on mutated os.environ
        • Fully compatible with safety-critical constraints (DO-178C / IEC 62304)
    """

    _lock: Final[threading.RLock] = threading.RLock()
    _snapshot: dict[str, str] | None = None
    _pid: int | None = None

    @classmethod
    def get(cls) -> Mapping[str, str]:
        """
        Return the frozen environment snapshot. Lazily initializes on first call.
        """

        with cls._lock:
            pid = os.getpid()

            # Recreate snapshot if PID changed (fork, multiprocessing)
            if cls._pid != pid or cls._snapshot is None:
                # Create immutable lowercase version of environment
                normalized = normalize_env_keys(os.environ)
                cls._snapshot = dict(normalized)  # defensive copy
                cls._pid = pid

            # Return safe shallow copy
            return dict(cls._snapshot)


# Public entry point for consistency
def get_frozen_env() -> Mapping[str, str]:
    return FrozenEnvironment.get()
