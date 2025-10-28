"""
Quantum Core Configuration Runtime State
────────────────────────────────────────────────────────────────────────────────
Encapsulates the in-process configuration state, ensuring atomicity,
thread safety, and consistency across concurrent threads.

Responsibilities
----------------
- Maintain a per-process snapshot of the active configuration environment.
- Provide atomic read/write operations through an internal lock.
- Expose immutable snapshots for inspection and debugging.
- Serve as the foundation for ConfigManager caching and environment layering.

Design Principles
-----------------
- **Single Responsibility** : isolates state management logic.
- **Encapsulation** : no global variables or uncontrolled mutations.
- **Thread Safety** : internal RLock ensures serialized access.
- **Transparency** : exposes safe snapshot methods for observability.
- **Immutability Contract** : always returns copies, never references.
"""

from __future__ import annotations

import os
import threading
from collections.abc import Callable
from pathlib import Path
from typing import Any, ClassVar, Final, TypeVar

T = TypeVar("T")


class ConfigState:
    """
    Thread-safe singleton encapsulating configuration state.

    This object holds runtime information about:
        - base_dir:   root directory from which .env files were resolved
        - loaded_pid: process identifier under which the environment was loaded
        - env_cache:  last resolved and merged environment dictionary

    Access Pattern
    --------------
        state = ConfigState.instance()
        snapshot = state.snapshot()
        state.update(base_dir=Path("/opt/app"), env_cache={"FOO": "bar"})

    Thread Safety
    -------------
        - All read/write operations acquire the internal RLock.
        - No external code should manipulate attributes directly.
        - Intended to be used by ConfigManager and providers only.
    """

    _instance: ClassVar[ConfigState | None] = None
    _lock: ClassVar[threading.RLock] = threading.RLock()

    def __init__(self) -> None:
        # Base directory where the configuration was discovered (.env parent dir)
        self._base_dir: Path | None = None

        # Process ID that loaded this configuration (to detect forks or reloads)
        self._loaded_pid: int | None = None

        # Cached environment variables (merged result from providers)
        self._env_cache: dict[str, str] | None = None

    # -------------------------------------------------------------------------
    # Singleton Accessor
    # -------------------------------------------------------------------------
    @classmethod
    def instance(cls) -> ConfigState:
        """
        Get or create the singleton ConfigState instance.

        Returns:
            ConfigState: singleton instance.
        """
        with cls._lock:
            if cls._instance is None:
                cls._instance = cls()
            return cls._instance

    # -------------------------------------------------------------------------
    # Controlled Access
    # -------------------------------------------------------------------------
    def access(self, func: Callable[[], T]) -> T:
        """
        Execute a callable within a thread-safe lock context.

        Use this to perform compound operations atomically without
        exposing the internal lock to external callers.
        """
        with self._lock:
            return func()

    # -------------------------------------------------------------------------
    # Snapshot and Getters
    # -------------------------------------------------------------------------
    def snapshot(self) -> dict[str, Any]:
        """
        Return an immutable snapshot of the current configuration state.

        Returns:
            dict[str, Any]: A copy of the internal state suitable for diagnostics.
        """
        with self._lock:
            return {
                "base_dir": str(self._base_dir) if self._base_dir else None,
                "loaded_pid": self._loaded_pid,
                "env_cache": dict(self._env_cache or {}),
            }

    def get_env_cache(self) -> dict[str, str]:
        """
        Safely retrieve a copy of the environment cache.

        Returns:
            dict[str, str]: Copy of the merged environment variables.
        """
        with self._lock:
            return dict(self._env_cache or {})

    # -------------------------------------------------------------------------
    # Mutators
    # -------------------------------------------------------------------------
    def update(
        self,
        *,
        base_dir: Path | None = None,
        loaded_pid: int | None = None,
        env_cache: dict[str, str] | None = None,
    ) -> None:
        """
        Atomically update parts of the configuration state.

        Args:
            base_dir: optional base directory.
            loaded_pid: optional process ID.
            env_cache: optional environment dictionary.
        """
        with self._lock:
            if base_dir is not None:
                self._base_dir = base_dir
            if loaded_pid is not None:
                self._loaded_pid = loaded_pid
            if env_cache is not None:
                self._env_cache = dict(env_cache)

    def reset(self) -> None:
        """
        Reset all internal state to None.

        Use this in tests or during a hard reload.
        """
        with self._lock:
            self._base_dir = None
            self._loaded_pid = None
            self._env_cache = None

    # -------------------------------------------------------------------------
    # Diagnostics Helpers
    # -------------------------------------------------------------------------
    def has_valid_cache(self) -> bool:
        """
        Determine whether the cache is valid for the current process.

        Returns:
            bool: True if cache is non-empty and PID matches current process.
        """
        with self._lock:
            return (
                self._loaded_pid == os.getpid()
                and isinstance(self._env_cache, dict)
                and bool(self._env_cache)
            )

    def describe(self) -> str:
        """
        Return a human-readable string describing the current state.

        Returns:
            str: diagnostic string (useful for logging/debugging).
        """
        snap = self.snapshot()
        base_dir = snap["base_dir"] or "<unset>"
        pid = snap["loaded_pid"] or "<unset>"
        env_size = len(snap["env_cache"] or {})
        return f"ConfigState(base_dir={base_dir}, pid={pid}, env_vars={env_size})"


# ╭─────────────────────────────────────────────────────────────────────────────╮
# │ Module-level constant for introspection (optional convenience)              │
# ╰─────────────────────────────────────────────────────────────────────────────╯
CONFIG_STATE: Final[ConfigState] = ConfigState.instance()
"""
Global access point for the process-local ConfigState.

Intended for diagnostic or read-only usage:
    from quantum.platform.config.runtime.state import CONFIG_STATE
    print(CONFIG_STATE.describe())
"""
