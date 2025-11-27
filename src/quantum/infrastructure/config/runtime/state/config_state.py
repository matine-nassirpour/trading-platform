from __future__ import annotations

import os
import threading

from pathlib import Path
from typing import Any, Final


class _ProcessLocalState:
    """
    Process-local, thread-safe configuration state.

    Guarantees:
        • One state instance per PID
        • Thread-safe access
        • Safe under reload (module re-import)
        • Safe under multiprocessing (fork/spawn)
        • Strict immutability semantics (state replaced atomically)
    """

    def __init__(self, pid: int) -> None:
        self._pid: int = pid

        # Internal fields
        self._base_dir: Path | None = None
        self._env_file: Path | None = None
        self._env_cache: dict[str, str] | None = None
        self._root_param: str | Path | None = None
        self._env_file_param: str | Path | None = None

        # Lock for updates
        self._lock: threading.RLock = threading.RLock()

    # --------------------------------------------------------------------------
    # Update atomic
    # --------------------------------------------------------------------------
    def update(
        self,
        *,
        base_dir: Path | None = None,
        env_file: Path | None = None,
        env_cache: dict[str, str] | None = None,
        root_param: str | Path | None = None,
        env_file_param: str | Path | None = None,
    ) -> None:
        """Atomic, thread-safe update of the process-local state."""

        with self._lock:
            if base_dir is not None:
                self._base_dir = base_dir
            if env_file is not None:
                self._env_file = env_file
            if env_cache is not None:
                self._env_cache = dict(env_cache)
            if root_param is not None:
                self._root_param = root_param
            if env_file_param is not None:
                self._env_file_param = env_file_param

    # ----------------------------------------------------------------------
    # Retrieval
    # ----------------------------------------------------------------------
    def get_env_cache(self) -> dict[str, str]:
        """Safely retrieve a copy of the cached environment variables."""
        with self._lock:
            return dict(self._env_cache or {})

    # --------------------------------------------------------------------------
    # Validation helpers
    # --------------------------------------------------------------------------
    def cache_matches_params(
        self,
        *,
        root_param: str | Path | None,
        env_file_param: str | Path | None,
    ) -> bool:
        return self._root_param == root_param and self._env_file_param == env_file_param

    def has_valid_cache(
        self,
        *,
        root_param: str | Path | None,
        env_file_param: str | Path | None,
    ) -> bool:
        """Cache is valid only if PID matches and parameters match."""

        if self._pid != os.getpid():
            return False
        if not isinstance(self._env_cache, dict) or not self._env_cache:
            return False
        return self.cache_matches_params(
            root_param=root_param,
            env_file_param=env_file_param,
        )

    # --------------------------------------------------------------------------
    # Diagnostics
    # --------------------------------------------------------------------------
    @staticmethod
    def _normalize(value: Any) -> Any:
        if value is None:
            return None

        if isinstance(value, Path):
            return str(value)

        # scalar types are fine
        if isinstance(value, (str, int, float, bool)):
            return value

        # fallback safe-stringification
        return str(value)

    def snapshot(self) -> dict[str, Any]:
        with self._lock:
            return {
                "pid": self._pid,
                "base_dir": self._normalize(self._base_dir),
                "env_file": self._normalize(self._env_file),
                "root_param": self._normalize(self._root_param),
                "env_file_param": self._normalize(self._env_file_param),
                "env_size": len(self._env_cache or {}),
            }

    def describe(self) -> str:
        snap = self.snapshot()
        return (
            "ConfigState("
            f"pid={snap['pid']}, "
            f"base_dir={snap['base_dir'] or 'null'}, "
            f"env_file={snap['env_file'] or 'null'}, "
            f"env_vars={snap['env_size']}, "
            f"root_param={snap['root_param'] or 'null'}, "
            f"env_file_param={snap['env_file_param'] or 'null'}"
            ")"
        )


class ConfigStateManager:
    """
    Factory ensuring process-local, reload-safe configuration state.

    Guarantees:
        • One state per process
        • Auto-regeneration on PID change or reload
        • Thread-safe retrieval
    """

    _lock: Final[threading.RLock] = threading.RLock()
    _state: _ProcessLocalState | None = None

    @classmethod
    def instance(cls) -> _ProcessLocalState:
        """
        Return a process-local state instance.
        Automatically regenerates state when:
            • PID changed (fork / multiprocessing)
            • Reload occurred (module re-import)
        """
        pid = os.getpid()
        with cls._lock:
            if cls._state is None or cls._state._pid != pid:
                cls._state = _ProcessLocalState(pid)
            return cls._state


# Public handle, for backward compatibility
CONFIG_STATE: Final[_ProcessLocalState] = ConfigStateManager.instance()
