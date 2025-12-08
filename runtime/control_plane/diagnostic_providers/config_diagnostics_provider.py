from __future__ import annotations

import os

from collections.abc import Mapping
from pathlib import Path
from typing import Any

from runtime.control_plane.diagnostic_providers.time_provider_dependency import (
    TimeProviderDependency,
)

from quantum.infrastructure.config.environment.core.normalization import (
    normalize_env_keys,
)
from quantum.infrastructure.config.environment.loading.loader import _load_env_files
from quantum.infrastructure.config.environment.loading.model_router import (
    EnvironmentModelRouter,
)
from quantum.infrastructure.config.environment.policy.strictness import (
    is_env_routing_strict,
)
from quantum.infrastructure.config.environment.resolution.namespace import (
    extract_application_env,
)
from quantum.infrastructure.config.environment.resolution.resolver import resolve_env
from quantum.infrastructure.config.models.core import CoreSettings
from quantum.infrastructure.config.models.logging import LoggingSettings
from quantum.infrastructure.config.models.mt5 import MT5Settings
from quantum.infrastructure.config.models.tracing import TracingSettings
from quantum.infrastructure.config.runtime.fsm.model import FSM_SCHEMA_VERSION
from quantum.infrastructure.config.runtime.manager import ConfigManager
from quantum.infrastructure.config.runtime.registry import CONFIG_MODELS
from quantum.infrastructure.config.runtime.state.config_state import CONFIG_STATE
from quantum.infrastructure.config.runtime.state.ready_cache import ReadyStateCache


class ConfigDiagnosticsProvider:
    """
    Unified diagnostic provider for the configuration subsystem.

    This adapter aggregates:
        • Readiness (READY state)
        • ConfigState diagnostics
        • Environment resolver & loader diagnostics
        • Effective model routing
        • Deep diff between OS env, .env, and final settings

    Fully read-only.
    Zero mutation.
    Safe for HTTP exposure or Streamlit dashboarding.
    """

    # --------------------------------------------------------------------------
    # High-level entrypoint
    # --------------------------------------------------------------------------
    @staticmethod
    def get_full_diagnostics(
        *,
        root: str | Path | None = None,
        env_file: str | Path | None = None,
    ) -> dict[str, Any]:
        """
        Returns a fully structured diagnostic block that can be serialized
        trivially to JSON or rendered in a Streamlit dashboard.
        """

        readiness = ConfigDiagnosticsProvider._diag_readiness()
        state = ConfigDiagnosticsProvider._diag_config_state()
        resolution = ConfigDiagnosticsProvider._diag_env_resolution(
            root=root, env_file=env_file
        )
        env_loading = ConfigDiagnosticsProvider._diag_env_loading(resolution)
        routing = ConfigDiagnosticsProvider._diag_model_routing(env_loading)
        final = ConfigDiagnosticsProvider._diag_final_settings()

        return {
            "schema_version": FSM_SCHEMA_VERSION,
            "timestamp_utc": TimeProviderDependency.get().now_utc().isoformat(),
            "readiness": readiness,
            "config_state": state,
            "env_resolution": resolution,
            "env_loading": env_loading,
            "routing": routing,
            "final_settings": final,
        }

    # --------------------------------------------------------------------------
    # Ready state
    # --------------------------------------------------------------------------
    @staticmethod
    def _diag_readiness() -> dict | None:
        state = ReadyStateCache.get()
        fp = ReadyStateCache.get_fingerprint()

        if state is None or fp is None:
            return None

        return {
            "fingerprint": fp,
            "status": state.status.value,
            "env": state.env,
            "settings": state.settings,
            "metadata": state.metadata,
        }

    # --------------------------------------------------------------------------
    # ConfigState diagnostics
    # --------------------------------------------------------------------------
    @staticmethod
    def _diag_config_state() -> dict[str, Any]:
        snap = CONFIG_STATE.snapshot()

        return {
            "pid": snap["pid"],
            "base_dir": snap["base_dir"],
            "env_file": snap["env_file"],
            "env_size": snap["env_size"],
            "root_param": snap["root_param"],
            "env_file_param": snap["env_file_param"],
            "strict_env_routing": is_env_routing_strict(),
        }

    # --------------------------------------------------------------------------
    # Environment resolver diagnostics
    # --------------------------------------------------------------------------
    @staticmethod
    def _diag_env_resolution(
        *,
        root: str | Path | None,
        env_file: str | Path | None,
    ) -> dict[str, Any]:
        res = resolve_env(root=root, env_file=env_file)

        # Files present in the base directory
        try:
            files = sorted(os.listdir(res.base_dir))
        except Exception:
            files = None

        return {
            "base_dir": str(res.base_dir),
            "env_file": str(res.env_file) if res.env_file else None,
            "available_files": files,
            "quantum_env": (os.getenv("QUANTUM_ENV") or "dev").strip().lower(),
        }

    # --------------------------------------------------------------------------
    # Environment loading diagnostics
    # --------------------------------------------------------------------------
    @staticmethod
    def _diag_env_loading(
        resolution,
    ) -> dict[str, Any]:
        # Raw file env (before OS merge)
        raw_file = _load_env_files(
            base_dir=resolution["base_dir"],
            env_file=resolution["env_file"],
        )

        normalized_file = normalize_env_keys(raw_file)
        normalized_os = normalize_env_keys(os.environ)

        # effective merge as per system rules
        merged = {**normalized_os, **normalized_file}
        effective = extract_application_env(merged, models=CONFIG_MODELS.models)

        return {
            "raw_file_env": raw_file,
            "normalized_file_env": normalized_file,
            "normalized_os_env_subset": {
                k: normalized_os[k] for k in sorted(normalized_os)[:80]
            },
            "merged": merged,
            "effective": effective,
            "file_env_size": len(normalized_file),
            "os_env_size": len(normalized_os),
            "effective_size": len(effective),
        }

    # --------------------------------------------------------------------------
    # Routing diagnostics
    # --------------------------------------------------------------------------
    @staticmethod
    def _diag_model_routing(env_loading_diag: Mapping[str, Any]) -> dict[str, Any]:
        effective = env_loading_diag["effective"]

        models = {
            "core": CoreSettings,
            "logging": LoggingSettings,
            "tracing": TracingSettings,
            "mt5": MT5Settings,
        }

        routed = EnvironmentModelRouter.route(models, effective)

        return {
            "routed_env": routed,
            "core_fields": list(models["core"].model_fields.keys()),
            "logging_fields": list(models["logging"].model_fields.keys()),
            "tracing_fields": list(models["tracing"].model_fields.keys()),
            "mt5_fields": list(models["mt5"].model_fields.keys()),
        }

    # --------------------------------------------------------------------------
    # Final settings diagnostics (Pydantic validated models)
    # --------------------------------------------------------------------------
    @staticmethod
    def _diag_final_settings() -> dict[str, Any]:
        """
        Extract final validated settings (non-cached versions).
        This ensures Streamlit shows what READY state will show.
        """

        core = ConfigManager.load_core_cached()
        logging = ConfigManager.load_logging_cached()
        tracing = ConfigManager.load_tracing_cached()
        mt5 = ConfigManager.load_mt5_cached()

        return {
            "core": core.model_dump(),
            "logging": logging.model_dump(),
            "tracing": tracing.model_dump(),
            "mt5": mt5.model_dump(),
        }
