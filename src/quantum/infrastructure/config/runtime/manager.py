from __future__ import annotations

import logging

from collections.abc import Mapping
from pathlib import Path
from typing import Any, Final, cast

from quantum.infrastructure.config.models.core import CoreSettings
from quantum.infrastructure.config.models.logging import LoggingSettings
from quantum.infrastructure.config.models.mt5 import MT5Settings
from quantum.infrastructure.config.models.tracing import TracingSettings
from quantum.infrastructure.config.runtime.fsm.model import ConfigFSMState
from quantum.infrastructure.config.runtime.fsm.orchestrator import ConfigFSMOrchestrator
from quantum.infrastructure.config.runtime.state.ready_cache import ReadyStateCache

LOGGER: Final = logging.getLogger("quantum.config.manager")


class ConfigManager:
    """
    High-level configuration façade using the FSM + ReadyStateCache architecture.

    Responsibilities:
        • Preserve the original public API (backward compatible)
        • Route configuration loading through the FSM orchestrator
        • Store a canonical READY state in ReadyStateCache
        • Derive Core/Logging/Tracing/MT5 settings from READY state
        • Provide both cached and non-cached getters

    All configuration now flows through:
        I/O → Adapters → FSM Pipeline (pure) → READY state → extraction
    """

    _orchestrator: Final[ConfigFSMOrchestrator] = ConfigFSMOrchestrator()

    # --------------------------------------------------------------------------
    # Subsystem Bootstrapper
    # --------------------------------------------------------------------------
    @staticmethod
    def run_fsm(
        *,
        root: str | Path | None = None,
        env_file: str | Path | None = None,
    ) -> ConfigFSMState:
        """
        Execute the full FSM lifecycle and return a READY state.
        This ALWAYS returns a ConfigFSMState in READY status.
        """
        return ConfigManager._orchestrator.run_full_lifecycle(
            root=root,
            env_file=env_file,
        )

    # --------------------------------------------------------------------------
    # Internal helpers
    # --------------------------------------------------------------------------
    @staticmethod
    def _get_ready_state() -> ConfigFSMState:
        """
        Retrieve the current READY state from cache, or compute and store it.

        This ensures:
            • Deterministic loading
            • Single canonical READY snapshot for the process
        """
        state = ReadyStateCache.get()
        if state is not None:
            return state

        state = ConfigManager.run_fsm()
        ReadyStateCache.set(state)
        return state

    @staticmethod
    def _extract_settings_group(
        state: ConfigFSMState,
        *,
        group: str,
    ) -> Mapping[str, Any]:
        """
        Extract a subgroup (core, logging, tracing, mt5) from READY.state.settings
        """
        if not state.settings:
            raise RuntimeError("READY state has no settings dictionary.")

        if group not in state.settings:
            raise KeyError(f"Settings group '{group}' not found in READY state.")

        value = state.settings[group]
        if not isinstance(value, Mapping):
            raise TypeError(
                f"Settings group '{group}' is not a mapping (got {type(value).__name__})."
            )

        return cast(Mapping[str, Any], value)

    # --------------------------------------------------------------------------
    # Cached Loaders
    # --------------------------------------------------------------------------
    @staticmethod
    def load_core_cached() -> CoreSettings:
        state = ConfigManager._get_ready_state()
        core_dict = ConfigManager._extract_settings_group(state, group="core")
        return CoreSettings(**core_dict)

    @staticmethod
    def load_logging_cached() -> LoggingSettings:
        state = ConfigManager._get_ready_state()
        log_dict = ConfigManager._extract_settings_group(state, group="logging")
        return LoggingSettings(**log_dict)

    @staticmethod
    def load_tracing_cached() -> TracingSettings:
        state = ConfigManager._get_ready_state()
        tr_dict = ConfigManager._extract_settings_group(state, group="tracing")
        return TracingSettings(**tr_dict)

    @staticmethod
    def load_mt5_cached() -> MT5Settings:
        state = ConfigManager._get_ready_state()
        mt5_dict = ConfigManager._extract_settings_group(state, group="mt5")
        return MT5Settings(**mt5_dict)

    # --------------------------------------------------------------------------
    # Non-cached public API
    # --------------------------------------------------------------------------
    @staticmethod
    def load_core(*, env: Mapping[str, Any] | None = None) -> CoreSettings:
        if env is not None:
            # Non-cached path bypasses READY-state cache entirely
            return CoreSettings(**env)
        return ConfigManager.load_core_cached()

    @staticmethod
    def load_logging(*, env: Mapping[str, Any] | None = None) -> LoggingSettings:
        if env is not None:
            return LoggingSettings(**env)
        return ConfigManager.load_logging_cached()

    @staticmethod
    def load_tracing(*, env: Mapping[str, Any] | None = None) -> TracingSettings:
        if env is not None:
            return TracingSettings(**env)
        return ConfigManager.load_tracing_cached()

    @staticmethod
    def load_mt5(*, env: Mapping[str, Any] | None = None) -> MT5Settings:
        if env is not None:
            return MT5Settings(**env)
        return ConfigManager.load_mt5_cached()
