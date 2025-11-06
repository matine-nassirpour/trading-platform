from __future__ import annotations

import logging
from threading import RLock
from typing import cast

from quantum.application.dto.config_bundle import QuantumConfigBundle
from quantum.application.ports.outbound.config_port import ConfigPort
from quantum.contracts.settings_contracts import (
    CoreSettingsContract,
    LoggingSettingsContract,
    MT5SettingsContract,
    TracingSettingsContract,
)
from quantum.infrastructure.config.providers.env_loader import load_env
from quantum.infrastructure.config.runtime.manager import ConfigManager
from quantum.infrastructure.config.runtime.state import ConfigState

_logger = logging.getLogger(__name__)

# Global lock to ensure thread-safe reinitialization
_INIT_LOCK = RLock()


class ConfigAdapter(ConfigPort):
    """
    Concrete implementation of ConfigPort backed by the
    Quantum infrastructure configuration system.
    """

    def __init__(self) -> None:
        self._state = ConfigState.instance()
        self._initialized = False

    # --------------------------------------------------------------------------
    # Internal helpers
    # --------------------------------------------------------------------------
    @staticmethod
    def _initialize_env() -> None:
        """
        Load and apply environment variables from all supported layers.
        Idempotent and safe for repeated calls.
        """
        try:
            load_env(apply=True, override=False)
            _logger.debug("Environment successfully loaded via EnvProvider.")
        except Exception as exc:
            _logger.exception("Failed to load environment: %s", exc)
            raise RuntimeError(f"ConfigProviderAdapter init_env failed: {exc}") from exc

    @staticmethod
    def _load_bundle() -> QuantumConfigBundle:
        """
        Construct and return a QuantumConfigBundle built from validated
        configuration models managed by ConfigManager.
        """
        try:
            core = cast(CoreSettingsContract, cast(object, ConfigManager.load()))
            logging_cfg = cast(
                LoggingSettingsContract, cast(object, ConfigManager.load_logging())
            )
            tracing_cfg = cast(
                TracingSettingsContract, cast(object, ConfigManager.load_tracing())
            )
            mt5_cfg = cast(MT5SettingsContract, cast(object, ConfigManager.load_mt5()))

            bundle = QuantumConfigBundle(
                core=core,
                logging=logging_cfg,
                tracing=tracing_cfg,
                mt5=mt5_cfg,
            )

            _logger.debug(
                "QuantumConfigBundle constructed successfully: "
                f"{bundle.core.quantum_app_name} ({bundle.core.quantum_env})"
            )
            return bundle

        except Exception as exc:
            _logger.exception("Failed to construct QuantumConfigBundle: %s", exc)
            raise RuntimeError(
                f"ConfigProviderAdapter bundle load failed: {exc}"
            ) from exc

    # --------------------------------------------------------------------------
    # Public API (implements ConfigPort)
    # --------------------------------------------------------------------------
    def get_bundle(self) -> QuantumConfigBundle:
        """
        Retrieve the current configuration bundle.

        Loads environment and configuration models lazily if not already
        initialized, ensuring idempotence and thread safety.
        """
        with _INIT_LOCK:
            if not self._initialized:
                self._initialize_env()
                self._initialized = True

            _logger.debug("Loading Quantum configuration bundle...")
            return self._load_bundle()

    def refresh_bundle(self) -> QuantumConfigBundle:
        """
        Force a full environment reload and configuration refresh.
        Clears caches, resets runtime state, and rebuilds the bundle.
        """
        with _INIT_LOCK:
            _logger.info("Refreshing Quantum configuration bundle...")
            ConfigManager.clear_caches()
            self._state.reset()
            self._initialize_env()
            return self._load_bundle()
