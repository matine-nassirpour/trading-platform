from __future__ import annotations

import os
import threading

from pathlib import Path
from typing import Any, Final

_thread_local = threading.local()


def _get_thread_scratchpad() -> dict:
    """
    Thread-local scratchpad used only for ephemeral diagnostics.
    Never authoritative. Never cached. Zero side effects.
    """
    d = getattr(_thread_local, "scratchpad", None)
    if d is None:
        d = {}
        _thread_local.scratchpad = d
    return d


class _ProcessLocalState:
    """
    Process-local, thread-safe configuration state.

    Guarantees:
        • Fork-safe: state re-initialized automatically after fork
        • Thread-safe: internal RLock protects updates
        • Process-coherent: PID is authoritative identity
        • Scratchpad separated from authoritative state
        • Atomic state replacement (no partial state)
    """

    def __init__(self, pid: int) -> None:
        self._pid: int = pid

        # Authoritative fields
        self._base_dir: Path | None = None
        self._env_file: Path | None = None
        self._env_cache: dict[str, str] | None = None
        self._root_param: str | Path | None = None
        self._env_file_param: str | Path | None = None

        # Lock for updates
        self._state_lock: threading.RLock = threading.RLock()

    # --------------------------------------------------------------------------
    # Fork handler (POSIX)
    # --------------------------------------------------------------------------
    def __enter_fork_child__(self) -> None:
        """
        Called automatically after os.fork().
        Must reset state cleanly to avoid sharing corrupted locks or state.
        """
        with self._state_lock:
            self._pid = os.getpid()
            self._base_dir = None
            self._env_file = None
            self._env_cache = None
            self._root_param = None
            self._env_file_param = None

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

        with self._state_lock:
            if base_dir is not None:
                self._base_dir = base_dir

            if env_file is not None:
                self._env_file = env_file

            if env_cache is not None:
                # Atomic replace
                self._env_cache = dict(env_cache)

            if root_param is not None:
                self._root_param = root_param

            if env_file_param is not None:
                self._env_file_param = env_file_param

    # ----------------------------------------------------------------------
    # Getters (thread-safe)
    # ----------------------------------------------------------------------
    def get_env_cache(self) -> dict[str, str]:
        """Safely retrieve a copy of the cached environment variables."""
        with self._state_lock:
            return dict(self._env_cache or {})

    # --------------------------------------------------------------------------
    # Cache validation
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
        with self._state_lock:
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
        with self._state_lock:
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
    Produces and manages the authoritative process-local state.

    New features:
        • auto-regeneration on PID change
        • fork-safe through os.register_at_fork
        • thread-safe access
    """

    _global_lock: Final[threading.RLock] = threading.RLock()
    _state: _ProcessLocalState | None = None

    @classmethod
    def _init_state(cls) -> _ProcessLocalState:
        pid = os.getpid()
        return _ProcessLocalState(pid)

    @classmethod
    def instance(cls) -> _ProcessLocalState:
        pid = os.getpid()

        with cls._global_lock:
            if cls._state is None:
                cls._state = cls._init_state()
                return cls._state

            # PID changed → fork detected
            if cls._state._pid != pid:
                cls._state = cls._init_state()
                return cls._state

            return cls._state


# Register fork handlers (POSIX only)
if hasattr(os, "register_at_fork"):
    os.register_at_fork(
        after_in_child=lambda: ConfigStateManager.instance().__enter_fork_child__()
    )

# Public backwards-compatible export
CONFIG_STATE: Final[_ProcessLocalState] = ConfigStateManager.instance()
