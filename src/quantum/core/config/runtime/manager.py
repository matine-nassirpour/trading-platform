"""
Quantum Core Configuration Manager
────────────────────────────────────────────────────────────────────────────────
Unified runtime facade for configuration management across the Quantum platform.

Responsibilities
----------------
- Load and validate structured configuration models (Pydantic-based).
- Orchestrate environment discovery through the provider layer.
- Manage process-safe caching and state consistency via ConfigState.
- Expose immutable, validated configuration objects for all subsystems.
- Provide inspection and snapshot utilities for observability and diagnostics.

Design Principles
-----------------
- **Single Responsibility** : orchestrates configuration lifecycle only.
- **Clean Architecture** : depends solely on core models and providers.
- **Thread Safe** : relies on ConfigState synchronization and LRU caching.
- **Immutability** : returns frozen, deterministic models.
- **Transparency** : exposes explicit snapshot and cache management APIs.
- **Extensibility** : open to integration of new configuration models.
"""

from __future__ import annotations

import logging
import os
from collections.abc import Mapping
from functools import lru_cache
from pathlib import Path
from typing import Final

from quantum.core.config.models.core import CoreSettings
from quantum.core.config.models.logging import LoggingSettings
from quantum.core.config.models.mt5 import MT5Settings
from quantum.core.config.models.tracing import TracingSettings
from quantum.core.config.providers.env_loader import load_env
from quantum.core.config.runtime.state import ConfigState

_LOGGER: Final = logging.getLogger("quantum.config.manager")


class ConfigManager:
    """
    Thread-safe, process-stable facade for configuration management.

    Exposes unified access to all configuration models (core, logging,
    tracing, brokers) and utilities for cache management.
    """

    # -------------------------------------------------------------------------
    # Internal helpers
    # -------------------------------------------------------------------------
    @staticmethod
    def _normalize_env(env: Mapping[str, str] | None = None) -> dict[str, str]:
        """Normalize environment keys to lowercase for Pydantic model compatibility."""
        return {k.lower(): v for k, v in (env or os.environ).items()}

    # -------------------------------------------------------------------------
    # Core loader
    # -------------------------------------------------------------------------
    @staticmethod
    @lru_cache
    def load(
        root: str | Path | None = None,
        *,
        env_file: str | Path | None = None,
        override: bool = False,
        env: Mapping[str, str] | None = None,
        apply: bool = False,
    ) -> CoreSettings:
        """
        Load the core configuration model.

        Steps:
            1. Load .env layers through provider.
            2. Merge with os.environ and explicit overrides.
            3. Validate and instantiate CoreSettings.

        Args:
            root: optional root directory.
            env_file: optional explicit .env file path.
            override: whether to override os.environ keys.
            env: optional mapping of explicit environment variables.
            apply: whether to apply merged envs to os.environ.

        Returns:
            CoreSettings: validated and frozen settings model.
        """
        merged = load_env(root, env_file, override=override, apply=apply)
        effective_env = {**merged, **os.environ, **(env or {})}
        settings = CoreSettings(**effective_env)

        _LOGGER.info(
            "Core settings loaded",
            extra={
                "attrs": {"app": settings.quantum_app_name, "env": settings.quantum_env}
            },
        )
        return settings

    # -------------------------------------------------------------------------
    # Singleton Accessor
    # -------------------------------------------------------------------------
    @staticmethod
    @lru_cache
    def load_logging(env: Mapping[str, str] | None = None) -> LoggingSettings:
        """Load and validate logging configuration."""
        return LoggingSettings(**ConfigManager._normalize_env(env))

    @staticmethod
    @lru_cache
    def load_tracing(env: Mapping[str, str] | None = None) -> TracingSettings:
        """Load and validate tracing configuration."""
        return TracingSettings(**ConfigManager._normalize_env(env))

    @staticmethod
    @lru_cache
    def load_mt5(env: Mapping[str, str] | None = None) -> MT5Settings:
        """Load and validate broker connection configuration (MT5)."""
        return MT5Settings(**ConfigManager._normalize_env(env))

    # -------------------------------------------------------------------------
    # Cache management
    # -------------------------------------------------------------------------
    @staticmethod
    def clear_caches() -> None:
        """
        Clear all configuration caches and reset internal state.

        Intended for testing, reloads, or dynamic environment switching.
        """
        for fn in (
            ConfigManager.load,
            ConfigManager.load_logging,
            ConfigManager.load_tracing,
            ConfigManager.load_mt5,
        ):
            cache_clear = getattr(fn, "cache_clear", None)
            if callable(cache_clear):
                cache_clear()

        ConfigState.instance().reset()
        _LOGGER.info("ConfigManager caches cleared and ConfigState reset.")

    # -------------------------------------------------------------------------
    # Snapshot helpers
    # -------------------------------------------------------------------------
    @staticmethod
    def snapshot(
        settings: CoreSettings | None = None,
        tracing: TracingSettings | None = None,
    ) -> dict[str, str]:
        """
        Return a concise snapshot of current configuration context.

        Args:
            settings: optional CoreSettings instance.
            tracing:  optional TracingSettings instance.

        Returns:
            dict[str, str]: minimal immutable summary.
        """
        s = settings or ConfigManager.load()
        t = tracing or ConfigManager.load_tracing()

        return {
            "app": s.quantum_app_name,
            "version": s.quantum_app_version,
            "env": s.quantum_env,
            "trace_exporter": t.quantum_trace_exporter,
            "metrics_port": str(s.quantum_metrics_port),
        }

    # -------------------------------------------------------------------------
    # Convenience: credentials accessors
    # -------------------------------------------------------------------------
    @staticmethod
    def get_mt5_credentials(
        channel: str,
        env: Mapping[str, str] | None = None,
    ) -> dict[str, str]:
        """
        Retrieve broker credentials for a given MT5 channel (e.g., 'ftmo').

        Args:
            channel: broker identifier (lowercase).
            env: optional mapping for overrides.

        Returns:
            dict[str, str]: broker credentials dictionary.
        """
        model = ConfigManager.load_mt5(env=env)
        prefix = channel.lower()
        return {
            "login": str(getattr(model, f"quantum_mt5_{prefix}_login", "") or ""),
            "server": getattr(model, f"quantum_mt5_{prefix}_server", "") or "",
            "password": getattr(model, f"quantum_mt5_{prefix}_password", "") or "",
        }
