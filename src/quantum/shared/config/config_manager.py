"""
Quantum Configuration Manager
──────────────────────────────────────────────────────────────────────────────
Unified environment and settings loader for all Quantum components.
"""

from __future__ import annotations

import logging
import os
import threading
from collections.abc import Mapping
from functools import lru_cache
from pathlib import Path
from typing import Final, Literal

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from quantum.shared.config.observability_settings import ObservabilitySettings
from quantum.shared.config.telemetry_settings import TelemetrySettings

try:
    from dotenv import dotenv_values, find_dotenv
except ImportError:
    dotenv_values = None
    find_dotenv = None

_LOGGER: Final = logging.getLogger("quantum.config")

# ──────────────────────────────────────────────────────────────────────────────
# Internal State
# ──────────────────────────────────────────────────────────────────────────────

_INIT_LOCK: Final = threading.Lock()
_LOADED: bool = False
_BASE_DIR: Path | None = None

# ──────────────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────────────


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


# ─── Core Loader
def _load_env_files(
    root: str | Path | None = None,
    env_file: str | Path | None = None,
    *,
    override: bool = False,
    apply: bool = True,
) -> dict[str, str]:
    """
    Loads environment variables from .env files.

    Returns:
        dict[str, str]: The merged environment values.

    Args:
        apply: If True, apply merged envs to os.environ.
        override: If True, overwrite existing os.environ values.
    """
    global _LOADED, _BASE_DIR
    if _LOADED:
        return dict(os.environ)

    if dotenv_values is None:
        _LOGGER.warning("python-dotenv not installed; skipping .env loading")
        return dict(os.environ)

    with _INIT_LOCK:
        if _LOADED:
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
                os.environ[k] = v

        _LOADED = True
        _BASE_DIR = base_dir

        _LOGGER.info(
            "Environment loaded",
            extra={"attrs": {"base_dir": str(base_dir), "env": current_env}},
        )

        return merged


# ──────────────────────────────────────────────────────────────────────────────
# Unified Settings model
# ──────────────────────────────────────────────────────────────────────────────


class Settings(BaseSettings):
    """Structured, validated configuration."""

    # ─── Core identity
    quantum_app_name: str = Field("python_core")
    quantum_app_version: str = Field("0.0.0+dev")
    quantum_env: str = Field("dev")
    quantum_ns: str = Field("quantum")

    # ─── Tracing
    quantum_trace_exporter: Literal["otlp", "console", "none"] = "console"
    quantum_trace_otlp_endpoint: str = Field("http://127.0.0.1:4318")
    quantum_trace_sample: float = 1.0

    # ─── Metrics
    quantum_metrics_addr: str = "0.0.0.0"
    quantum_metrics_port: int = 0

    # ─── Execution policy
    quantum_exec_timeout: float = Field(5.0)
    quantum_exec_retries: int = Field(3)
    quantum_exec_backoff: float = Field(0.5)
    quantum_exec_backoff_max: float = Field(5.0)

    # ─── MT5 credentials
    quantum_mt5_ftmo_login: int | None = None
    quantum_mt5_ftmo_server: str | None = None
    quantum_mt5_ftmo_password: str | None = None
    quantum_mt5_fundednext_login: int | None = None
    quantum_mt5_fundednext_server: str | None = None
    quantum_mt5_fundednext_password: str | None = None

    # ─── Validation
    @field_validator("quantum_env", mode="before")
    @classmethod
    def normalize_env(cls, v):
        return str(v or "dev").strip().lower()

    @field_validator("quantum_trace_sample")
    @classmethod
    def validate_sample(cls, v):
        if not (0.0 <= v <= 1.0):
            raise ValueError("quantum_trace_sample must be in [0, 1]")
        return v

    @model_validator(mode="after")
    def validate_credentials(self):
        """Ensure complete MT5 credential triplets."""
        if self.quantum_mt5_ftmo_login and not all(
            [self.quantum_mt5_ftmo_server, self.quantum_mt5_ftmo_password]
        ):
            raise ValueError("Incomplete FTMO credentials.")
        if self.quantum_mt5_fundednext_login and not all(
            [self.quantum_mt5_fundednext_server, self.quantum_mt5_fundednext_password]
        ):
            raise ValueError("Incomplete FUNDEDNEXT credentials.")
        return self

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


# ──────────────────────────────────────────────────────────────────────────────
# Config Manager facade
# ──────────────────────────────────────────────────────────────────────────────


class ConfigManager:
    """Thread-safe facade for configuration management."""

    @staticmethod
    @lru_cache
    def load(
        root: str | Path | None = None,
        *,
        env_file: str | Path | None = None,
        override: bool = False,
        env: Mapping[str, str] | None = None,
    ) -> Settings:
        """Loads environment and returns validated Settings instance."""
        merged = _load_env_files(root, env_file, override=override, apply=(env is None))
        effective_env = {**merged, **(env or {})}

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
    def load_observability(
        env: Mapping[str, str] | None = None,
    ) -> ObservabilitySettings:
        """Loads and returns observability configuration."""
        return ObservabilitySettings(**(env or os.environ))

    @staticmethod
    @lru_cache
    def load_telemetry(env: Mapping[str, str] | None = None) -> TelemetrySettings:
        """Loads and returns telemetry configuration."""
        return TelemetrySettings(**(env or os.environ))

    @staticmethod
    def clear_caches() -> None:
        """Clears all cached configuration."""
        for fn in (
            ConfigManager.load,
            ConfigManager.load_observability,
            ConfigManager.load_telemetry,
        ):
            cache_clear = getattr(fn, "cache_clear", None)
            if callable(cache_clear):
                cache_clear()

    @staticmethod
    def snapshot(settings: Settings | None = None) -> dict[str, str]:
        """Returns a non-sensitive runtime configuration snapshot."""
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
        """Accesses MT5 credentials for a given execution channel."""
        settings = ConfigManager.load(env=env)
        prefix = channel.lower()
        return {
            "login": str(getattr(settings, f"quantum_mt5_{prefix}_login", "") or ""),
            "server": getattr(settings, f"quantum_mt5_{prefix}_server", "") or "",
            "password": getattr(settings, f"quantum_mt5_{prefix}_password", "") or "",
        }
