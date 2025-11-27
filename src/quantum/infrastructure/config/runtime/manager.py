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
from quantum.infrastructure.config.runtime.env_snapshot import get_frozen_env
from quantum.infrastructure.config.runtime.state import ConfigStateManager

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

    @staticmethod
    def _build_env_for_model(
        *,
        env_override: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        Build the effective environment for model loading.

        Structure:
            • base_env: produced by load_env(), cache-aware and PID-aware
            • frozen_os_env: immutable snapshot of os.environ (PID-aware)
            • env_override: direct model-specific inject (non-cached loaders only)

        All merges are deterministic and side-effect-free.
        """

        base_env = load_env()
        frozen_os_env = get_frozen_env()

        combined = {
            **base_env,  # priority 1: .env + fallback
            **frozen_os_env,  # priority 2: OS snapshot
            **(env_override or {}),  # priority 3: override for test/non-cached
        }

        return ConfigManager._normalize_env(combined)

    @staticmethod
    def _load_model(
        model_cls: type[Any],
        *,
        cached: bool,
        env_override: Mapping[str, Any] | None = None,
    ):
        """
        Generic, factorized loader for all configuration models.

        Guaranteed properties:
            • Fully deterministic
            • Optional override (non-cached)
            • Zero mutation
            • Clean Architecture compliant
        """

        if cached and env_override is None:

            @cache
            def _cached_loader() -> Any:
                env = ConfigManager._build_env_for_model()
                return model_cls(**env)

            return _cached_loader()

        env = ConfigManager._build_env_for_model(env_override=env_override)
        return model_cls(**env)

    # --------------------------------------------------------------------------
    # Public API: Cached Loaders
    # --------------------------------------------------------------------------
    @staticmethod
    def load_core_cached() -> CoreSettings:
        return ConfigManager._load_model(CoreSettings, cached=True)

    @staticmethod
    def load_logging_cached() -> LoggingSettings:
        return ConfigManager._load_model(LoggingSettings, cached=True)

    @staticmethod
    def load_tracing_cached() -> TracingSettings:
        return ConfigManager._load_model(TracingSettings, cached=True)

    @staticmethod
    def load_mt5_cached() -> MT5Settings:
        return ConfigManager._load_model(MT5Settings, cached=True)

    # --------------------------------------------------------------------------
    # Override / test loaders (override-friendly, non-cached)
    # --------------------------------------------------------------------------
    @staticmethod
    def load_core(*, env: Mapping[str, Any] | None = None) -> CoreSettings:
        return ConfigManager._load_model(CoreSettings, cached=False, env_override=env)

    @staticmethod
    def load_logging(*, env: Mapping[str, Any] | None = None) -> LoggingSettings:
        return ConfigManager._load_model(
            LoggingSettings, cached=False, env_override=env
        )

    @staticmethod
    def load_tracing(*, env: Mapping[str, Any] | None = None) -> TracingSettings:
        return ConfigManager._load_model(
            TracingSettings, cached=False, env_override=env
        )

    @staticmethod
    def load_mt5(*, env: Mapping[str, Any] | None = None) -> MT5Settings:
        return ConfigManager._load_model(MT5Settings, cached=False, env_override=env)

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

        ConfigStateManager.instance().update(
            base_dir=None,
            env_file=None,
            env_cache=None,
            root_param=None,
            env_file_param=None,
        )

        LOGGER.info("ConfigManager caches cleared and ConfigStateManager reset.")

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
