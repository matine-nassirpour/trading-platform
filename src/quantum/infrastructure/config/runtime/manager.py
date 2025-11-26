from __future__ import annotations

import logging
import os

from collections.abc import Mapping
from functools import cache
from typing import Any, Final

from quantum.infrastructure.config.models.core import CoreSettings
from quantum.infrastructure.config.models.logging import LoggingSettings
from quantum.infrastructure.config.models.mt5 import MT5Settings
from quantum.infrastructure.config.models.tracing import TracingSettings
from quantum.infrastructure.config.providers.env_loader import load_env
from quantum.infrastructure.config.runtime.state import ConfigState

LOGGER: Final = logging.getLogger("quantum.config.manager")


class ConfigManager:
    """
    Thread-safe, process-stable facade for configuration management.

    Exposes unified access to all configuration models (core, logging,
    tracing, brokers) and utilities for cache management.
    """

    # --------------------------------------------------------------------------
    # Internal helpers
    # --------------------------------------------------------------------------
    @staticmethod
    def _normalize_env(env: Mapping[str, str] | None) -> dict[str, str]:
        """Return env with normalized lowercase keys."""
        return {k.lower(): v for k, v in (env or os.environ).items()}

    # --------------------------------------------------------------------------
    # Production / Cacheable loaders
    # --------------------------------------------------------------------------
    @staticmethod
    @cache
    def load_core_cached() -> CoreSettings:
        """
        Load CoreSettings using environment loaded from files + process env.

        NOTE:
        - No parameters → safe for memoization.
        - Picks up the environment loaded via `load_env()`.
        """
        merged = load_env(apply=False, override=False)
        effective_env = {**merged, **os.environ}
        settings = CoreSettings(**ConfigManager._normalize_env(effective_env))

        LOGGER.info(
            "CoreSettings loaded (cached)",
            extra={
                "attrs": {"app": settings.quantum_app_name, "env": settings.quantum_env}
            },
        )
        return settings

    @staticmethod
    @cache
    def load_logging_cached() -> LoggingSettings:
        """Cached loader for LoggingSettings."""
        model = LoggingSettings(**ConfigManager._normalize_env(None))
        return model

    @staticmethod
    @cache
    def load_tracing_cached() -> TracingSettings:
        """Cached loader for TracingSettings."""
        model = TracingSettings(**ConfigManager._normalize_env(None))
        return model

    @staticmethod
    @cache
    def load_mt5_cached() -> MT5Settings:
        """Cached loader for MT5Settings."""
        model = MT5Settings(**ConfigManager._normalize_env(None))
        return model

    # --------------------------------------------------------------------------
    # Override / test loaders (no cache)
    # --------------------------------------------------------------------------
    @staticmethod
    def load_core(*, env: Mapping[str, Any] | None = None) -> CoreSettings:
        """Non-cached loader allowing explicit env overrides."""
        effective_env = {**os.environ, **(env or {})}
        return CoreSettings(**ConfigManager._normalize_env(effective_env))

    @staticmethod
    def load_logging(*, env: Mapping[str, Any] | None = None) -> LoggingSettings:
        """Non-cached override loader."""
        return LoggingSettings(**ConfigManager._normalize_env(env))

    @staticmethod
    def load_tracing(*, env: Mapping[str, Any] | None = None) -> TracingSettings:
        """Non-cached override loader."""
        return TracingSettings(**ConfigManager._normalize_env(env))

    @staticmethod
    def load_mt5(*, env: Mapping[str, Any] | None = None) -> MT5Settings:
        """Non-cached override loader."""
        return MT5Settings(**ConfigManager._normalize_env(env))

    # --------------------------------------------------------------------------
    # Cache management
    # --------------------------------------------------------------------------
    @staticmethod
    def clear_caches() -> None:
        """Clear all cached settings + runtime environment cache."""
        for fn in (
            ConfigManager.load_core_cached,
            ConfigManager.load_logging_cached,
            ConfigManager.load_tracing_cached,
            ConfigManager.load_mt5_cached,
        ):
            fn.cache_clear()

        ConfigState.instance().reset()
        LOGGER.info("ConfigManager caches cleared and ConfigState reset.")

    # --------------------------------------------------------------------------
    # Snapshot utils
    # --------------------------------------------------------------------------
    @staticmethod
    def snapshot(
        settings: CoreSettings | None = None,
        tracing: TracingSettings | None = None,
    ) -> dict[str, str]:
        """Return minimal configuration snapshot."""
        s = settings or ConfigManager.load_core_cached()
        t = tracing or ConfigManager.load_tracing_cached()

        return {
            "app": s.quantum_app_name,
            "version": s.quantum_app_version,
            "env": s.quantum_env,
            "trace_exporter": t.quantum_trace_exporter,
            "metrics_port": str(s.quantum_metrics_port),
        }

    # --------------------------------------------------------------------------
    # Broker Credential helper
    # --------------------------------------------------------------------------
    @staticmethod
    def get_mt5_credentials(
        channel: str,
        *,
        env: Mapping[str, str] | None = None,
        cached: bool = True,
    ) -> dict[str, str]:
        """
        Retrieve broker credentials for MT5.

        Args:
            channel: 'ftmo', 'fundednext', ...
            env: optional override env mapping.
            cached: whether to use cached MT5Settings.

        """
        model = (
            ConfigManager.load_mt5_cached()
            if cached and env is None
            else ConfigManager.load_mt5(env=env)
        )

        prefix = channel.lower()
        return {
            "login": str(getattr(model, f"quantum_mt5_{prefix}_login", "") or ""),
            "server": getattr(model, f"quantum_mt5_{prefix}_server", "") or "",
            "password": getattr(model, f"quantum_mt5_{prefix}_password", "") or "",
        }
