from runtime.control_plane.diagnostic_providers.time_provider_dependency import (
    TimeProviderDependency,
)

from quantum.infrastructure.config.environment.policy.constants import RESERVED_ENV_KEYS
from quantum.infrastructure.config.environment.system.snapshot import get_frozen_env
from quantum.infrastructure.config.runtime.fsm.model import FSM_SCHEMA_VERSION
from quantum.infrastructure.config.runtime.state.config_state import CONFIG_STATE
from quantum.infrastructure.config.runtime.state.ready_cache import ReadyStateCache


class ConfigDiagnosticsProvider:
    """
    Provides a unified, read-only diagnostic view of the configuration system.

    Combines:
        • The canonical READY configuration state (from ReadyStateCache)
        • The process-local loader state snapshot (from CONFIG_STATE)
        • Explicit exposure of reserved environment keys (OS-only)
        • Cache coherence indicators for observability

    Intended for monitoring and dashboards only.
    No mutation, no I/O, and no direct access to private internals.
    """

    @staticmethod
    def get_diagnostics() -> dict | None:
        time_provider = TimeProviderDependency.get()

        ready_config = ReadyStateCache.get()
        fp = ReadyStateCache.get_fingerprint()

        if ready_config is None or fp is None:
            return None

        loader_state = CONFIG_STATE
        snapshot = loader_state.snapshot()

        # evaluate cache health
        cache_matches_params = loader_state.cache_matches_params(
            root_param=snapshot["root_param"],
            env_file_param=snapshot["env_file_param"],
        )

        has_valid_cache = loader_state.has_valid_cache(
            root_param=snapshot["root_param"],
            env_file_param=snapshot["env_file_param"],
        )

        os_env = get_frozen_env()

        # Extract reserved keys (OS-only, not coming from .env files)
        reserved_keys = {
            key: os_env.get(key)  # may be None if OS didn't set it
            for key in RESERVED_ENV_KEYS
        }

        return {
            "schema_version": FSM_SCHEMA_VERSION,
            "fingerprint": fp,
            "timestamp_utc": time_provider.now_utc().isoformat(),
            "ready_state": {
                "status": ready_config.status.value,
                "env": ready_config.env,
                "settings": ready_config.settings,
                "metadata": ready_config.metadata,
            },
            "loader_snapshot": snapshot,
            "reserved_keys": reserved_keys,
            "cache_matches_params": cache_matches_params,
            "has_valid_cache": has_valid_cache,
        }
