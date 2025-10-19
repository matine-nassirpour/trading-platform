"""
Quantum Configuration Manager
──────────────────────────────────────────────────────────────────────────────
Unified environment and settings loader for all Quantum components.
Process-safe, thread-safe, and idempotent.
"""

from __future__ import annotations

import logging
import os
import threading
from collections.abc import Callable, Mapping
from functools import lru_cache
from pathlib import Path
from typing import ClassVar, Final, TypeVar

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from quantum.shared.config.logging_settings import LoggingSettings
from quantum.shared.config.mt5_settings import MT5Settings
from quantum.shared.config.tracing_settings import TracingSettings

try:
    from dotenv import dotenv_values, find_dotenv
except ImportError:
    dotenv_values = None
    find_dotenv = None

_LOGGER: Final = logging.getLogger("quantum.config")
T = TypeVar("T")

# ╭─────────────────────────────────────────────────────────────────────────────╮
# │ Internal State                                                              │
# ╰─────────────────────────────────────────────────────────────────────────────╯


class ConfigState:
    """
    Thread-safe singleton encapsulating configuration state.

    Responsibilities
    ----------------
    - Maintain process-local cache of configuration environment data.
    - Provide atomic access and update operations.
    - Guarantee consistency across concurrent threads within a single process.

    Design principles
    -----------------
    - Single Responsibility: isolates configuration state logic.
    - Thread Safety: internal lock protects state mutations.
    - Transparency: explicit getters/setters, no implicit globals.
    - Immutability contract: only copies are exposed to callers.
    """

    _instance: ClassVar[ConfigState | None] = None
    _lock: ClassVar[threading.RLock] = threading.RLock()

    def __init__(self) -> None:
        self._base_dir: Path | None = None
        self._loaded_pid: int | None = None
        self._env_cache: dict[str, str] | None = None

    # ─── Singleton Accessor
    @classmethod
    def instance(cls) -> ConfigState:
        with cls._lock:
            if cls._instance is None:
                cls._instance = cls()
            return cls._instance

    # ─── Safe execution context
    def access(self, func: Callable[[], T]) -> T:
        """
        Execute a callable within a thread-safe lock context.

        This provides controlled access to the internal lock
        without exposing it publicly.
        """
        with self._lock:
            return func()

    # ─── Getters (return copies for immutability)
    def snapshot(self) -> dict[str, str | int | dict[str, str] | None]:
        with self._lock:
            return {
                "base_dir": str(self._base_dir) if self._base_dir else None,
                "loaded_pid": self._loaded_pid,
                "env_cache": dict(self._env_cache or {}),
            }

    def get_env_cache(self) -> dict[str, str]:
        with self._lock:
            return dict(self._env_cache or {})

    # ─── Mutators (atomic updates)
    def update(
        self,
        *,
        base_dir: Path | None = None,
        loaded_pid: int | None = None,
        env_cache: dict[str, str] | None = None,
    ) -> None:
        with self._lock:
            if base_dir is not None:
                self._base_dir = base_dir
            if loaded_pid is not None:
                self._loaded_pid = loaded_pid
            if env_cache is not None:
                self._env_cache = dict(env_cache)

    def reset(self) -> None:
        with self._lock:
            self._base_dir = None
            self._loaded_pid = None
            self._env_cache = None


# ╭─────────────────────────────────────────────────────────────────────────────╮
# │ Helpers                                                                     │
# ╰─────────────────────────────────────────────────────────────────────────────╯


def _merge_envs(*layers: Mapping[str, str | None]) -> dict[str, str]:
    """Merge environment layers, ignoring None values."""
    merged: dict[str, str] = {}
    for layer in layers:
        for k, v in layer.items():
            if v is not None:
                merged[k] = v
    return merged


def _resolve_env_path(
    root: str | Path | None, env_file: str | Path | None
) -> tuple[Path | None, Path | None]:
    """Resolves base directory and explicit env file path."""
    if env_file:
        p = Path(env_file)
        if p.exists():
            return p.parent, p

    if root:
        return Path(root), None

    if find_dotenv is not None:
        found = find_dotenv(usecwd=True)
        if found:
            fp = Path(found)
            return fp.parent, fp

    return Path.cwd(), None


# ╭─────────────────────────────────────────────────────────────────────────────╮
# │ Core Loader                                                                 │
# ╰─────────────────────────────────────────────────────────────────────────────╯


def _load_env_files(
    root: str | Path | None = None,
    env_file: str | Path | None = None,
    *,
    override: bool = False,
    apply: bool = True,
) -> dict[str, str]:
    """
    Loads environment variables from .env files in a process-safe way.

    Returns:
        dict[str, str]: The merged environment values.
    """
    pid = os.getpid()
    state = ConfigState.instance()

    def _load_logic() -> dict[str, str]:
        snapshot = state.snapshot()
        env_cache = snapshot.get("env_cache")
        if snapshot["loaded_pid"] == pid and isinstance(env_cache, dict) and env_cache:
            return dict(env_cache)

        if dotenv_values is None:
            _LOGGER.warning("python-dotenv not installed; skipping .env loading")
            return dict(os.environ)

        base_dir, explicit_file = _resolve_env_path(root, env_file)
        if base_dir is None:
            base_dir = Path.cwd()

        env_base = (
            dotenv_values(explicit_file)
            if explicit_file
            else dotenv_values(base_dir / ".env")
        )
        current_env = os.getenv("QUANTUM_ENV") or (
            env_base.get("QUANTUM_ENV") if env_base else "dev"
        )
        env_specific = (
            dotenv_values(base_dir / f".env.{current_env}") if current_env else {}
        )
        env_local = dotenv_values(base_dir / ".env.local")

        merged = _merge_envs(env_base or {}, env_specific or {}, env_local or {})

        if apply:
            for k, v in merged.items():
                if k in os.environ and not override:
                    continue
                if k not in os.environ and v is not None:
                    os.environ.setdefault(k, v)

        state.update(base_dir=base_dir, loaded_pid=pid, env_cache=merged)

        _LOGGER.info(
            f"Environment loaded (pid={pid})",
            extra={"attrs": {"base_dir": str(base_dir), "env": current_env}},
        )
        return merged

    # Execute atomically under internal lock
    return state.access(_load_logic)


# ╭─────────────────────────────────────────────────────────────────────────────╮
# │ Unified Settings model                                                      │
# ╰─────────────────────────────────────────────────────────────────────────────╯


class Settings(BaseSettings):
    """Structured, validated configuration."""

    # ─── Core identity
    quantum_app_name: str = Field("python_core")
    quantum_app_version: str = Field("0.0.0+dev")
    quantum_env: str = Field("dev")
    quantum_ns: str = Field("quantum")
    quantum_instance_id: str | None = Field(None)

    # ─── Metrics
    quantum_metrics_addr: str = Field("0.0.0.0")
    quantum_metrics_port: int = Field(0)

    # ─── Execution policy
    quantum_exec_timeout: float = Field(5.0)
    quantum_exec_retries: int = Field(3)
    quantum_exec_backoff: float = Field(0.5)
    quantum_exec_backoff_max: float = Field(5.0)

    # ─── Validation
    @field_validator("quantum_env", mode="before")
    @classmethod
    def normalize_env(cls, v):
        return str(v or "dev").strip().lower()

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


# ╭─────────────────────────────────────────────────────────────────────────────╮
# │ Config Manager facade                                                       │
# ╰─────────────────────────────────────────────────────────────────────────────╯


class ConfigManager:
    """Thread-safe facade for configuration management."""

    @staticmethod
    def _normalize_env(env: Mapping[str, str] | None = None) -> dict[str, str]:
        """Normalize environment keys to lowercase for Pydantic BaseModel compatibility."""
        return {k.lower(): v for k, v in (env or os.environ).items()}

    # ─── Core runtime
    @staticmethod
    @lru_cache
    def load(
        root: str | Path | None = None,
        *,
        env_file: str | Path | None = None,
        override: bool = False,
        env: Mapping[str, str] | None = None,
    ) -> Settings:
        merged = _load_env_files(root, env_file, override=override, apply=False)
        effective_env = {**merged, **os.environ, **(env or {})}
        settings = Settings(**effective_env)

        _LOGGER.info(
            "Settings initialized",
            extra={
                "attrs": {"app": settings.quantum_app_name, "env": settings.quantum_env}
            },
        )
        return settings

    @staticmethod
    @lru_cache
    def load_logging(env: Mapping[str, str] | None = None) -> LoggingSettings:
        return LoggingSettings(**ConfigManager._normalize_env(env))

    @staticmethod
    @lru_cache
    def load_tracing(env: Mapping[str, str] | None = None) -> TracingSettings:
        return TracingSettings(**ConfigManager._normalize_env(env))

    @staticmethod
    @lru_cache
    def load_mt5(env: Mapping[str, str] | None = None) -> MT5Settings:
        return MT5Settings(**ConfigManager._normalize_env(env))

    # ─── Cache management
    @staticmethod
    def clear_caches() -> None:
        for fn in (
            ConfigManager.load,
            ConfigManager.load_logging,
            ConfigManager.load_tracing,
        ):
            cache_clear = getattr(fn, "cache_clear", None)
            if callable(cache_clear):
                cache_clear()
        ConfigState.instance().reset()
        _LOGGER.info("ConfigManager caches cleared and state reset")

    # ─── Snapshot helper
    @staticmethod
    def snapshot(settings: Settings | None = None) -> dict[str, str]:
        s = settings or ConfigManager.load()
        return {
            "app": s.quantum_app_name,
            "version": s.quantum_app_version,
            "env": s.quantum_env,
            "trace_exporter": s.quantum_trace_exporter,
            "metrics_port": str(s.quantum_metrics_port),
        }

    # ─── Credentials helper
    @staticmethod
    def get_mt5_credentials(
        channel: str, env: Mapping[str, str] | None = None
    ) -> dict[str, str]:
        settings = ConfigManager.load(env=env)
        prefix = channel.lower()
        return {
            "login": str(getattr(settings, f"quantum_mt5_{prefix}_login", "") or ""),
            "server": getattr(settings, f"quantum_mt5_{prefix}_server", "") or "",
            "password": getattr(settings, f"quantum_mt5_{prefix}_password", "") or "",
        }
