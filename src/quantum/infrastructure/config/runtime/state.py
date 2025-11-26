from __future__ import annotations

import os
import threading

from pathlib import Path
from typing import Any, ClassVar, Final


class ConfigState:
    """
    Thread-safe singleton encapsulating configuration state.

    Now tracks full environment loading fingerprint:
        - PID
        - provided root/env_file parameters
        - resolved base_dir and resolved_env_file
        - merged env cache

    This ensures deterministic, parameter-sensitive caching.
    """

    _instance: ClassVar[ConfigState | None] = None
    _lock: ClassVar[threading.RLock] = threading.RLock()

    def __init__(self) -> None:
        # Detected environment state & cache
        self._base_dir: Path | None = None
        self._env_file: Path | None = None
        self._env_cache: dict[str, str] | None = None
        self._loaded_pid: int | None = None

        # Parameters used to compute the cache
        self._root_param: str | Path | None = None
        self._env_file_param: str | Path | None = None

    # --------------------------------------------------------------------------
    # Singleton Accessor
    # --------------------------------------------------------------------------
    @classmethod
    def instance(cls) -> ConfigState:
        """Get or create the singleton ConfigState instance."""
        with cls._lock:
            if cls._instance is None:
                cls._instance = cls()
            return cls._instance

    # --------------------------------------------------------------------------
    # Mutators
    # --------------------------------------------------------------------------
    def update(
        self,
        *,
        base_dir: Path | None = None,
        env_file: Path | None = None,
        env_cache: dict[str, str] | None = None,
        loaded_pid: int | None = None,
        root_param: str | Path | None = None,
        env_file_param: str | Path | None = None,
    ) -> None:
        """
        Atomically update the configuration state, including parameter fingerprint.
        """
        with self._lock:
            if base_dir is not None:
                self._base_dir = base_dir
            if env_file is not None:
                self._env_file = env_file
            if env_cache is not None:
                # defensive copy
                self._env_cache = dict(env_cache)
            if loaded_pid is not None:
                self._loaded_pid = loaded_pid
            if root_param is not None:
                self._root_param = root_param
            if env_file_param is not None:
                self._env_file_param = env_file_param

    def reset(self) -> None:
        """Reset the config state completely."""
        with self._lock:
            self._base_dir = None
            self._env_file = None
            self._env_cache = None
            self._loaded_pid = None
            self._root_param = None
            self._env_file_param = None

    # ----------------------------------------------------------------------
    # Cache accessors
    # ----------------------------------------------------------------------
    def get_env_cache(self) -> dict[str, str]:
        """Safely retrieve a copy of the cached environment variables."""

        with self._lock:
            return dict(self._env_cache or {})

    # --------------------------------------------------------------------------
    # Validation
    # --------------------------------------------------------------------------
    def cache_matches_params(
        self,
        *,
        root_param: str | Path | None,
        env_file_param: str | Path | None,
    ) -> bool:
        """Check if parameters match the cached fingerprint."""

        return self._root_param == root_param and self._env_file_param == env_file_param

    def has_valid_cache(
        self,
        *,
        root_param: str | Path | None,
        env_file_param: str | Path | None,
    ) -> bool:
        """
        Determine if cache is valid for:
            - current PID
            - provided root/env_file parameters
            - non-empty env cache
        """

        with self._lock:
            if self._loaded_pid != os.getpid():
                return False
            if not isinstance(self._env_cache, dict) or not self._env_cache:
                return False
            if not self.cache_matches_params(
                root_param=root_param,
                env_file_param=env_file_param,
            ):
                return False
            return True

    # ----------------------------------------------------------------------
    # Snapshot & diagnostics
    # ----------------------------------------------------------------------
    def snapshot(self) -> dict[str, Any]:
        with self._lock:
            return {
                "base_dir": str(self._base_dir) if self._base_dir else None,
                "env_file": str(self._env_file) if self._env_file else None,
                "root_param": str(self._root_param),
                "env_file_param": str(self._env_file_param),
                "loaded_pid": self._loaded_pid,
                "env_size": len(self._env_cache or {}),
            }

    def describe(self) -> str:
        snap = self.snapshot()
        return (
            f"ConfigState(pid={snap['loaded_pid']}, "
            f"base_dir={snap['base_dir']}, "
            f"env_file={snap['env_file']}, "
            f"env_vars={snap['env_size']}, "
            f"root_param={snap['root_param']}, "
            f"env_file_param={snap['env_file_param']})"
        )


CONFIG_STATE: Final[ConfigState] = ConfigState.instance()
