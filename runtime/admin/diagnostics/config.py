from dataclasses import dataclass
from typing import Any

from quantum.infrastructure.config.environment.policy.constants import RESERVED_ENV_KEYS
from quantum.infrastructure.config.environment.system.snapshot import get_frozen_env
from quantum.infrastructure.config.runtime.fsm.model import FSM_SCHEMA_VERSION
from quantum.infrastructure.config.runtime.state.config_state import CONFIG_STATE
from quantum.infrastructure.config.runtime.state.ready_cache import ReadyStateCache


@dataclass(frozen=True)
class ConfigDiagnosticsSnapshot:
    """
    Immutable, canonical snapshot of the configuration subsystem state.

    Contract:
    - Safe for external exposure (dashboards, admin APIs).
    - NEVER raises during construction.
    - Missing or unavailable data is represented explicitly.
    """

    schema_version: str

    ready: bool
    fingerprint: str | None

    ready_state: dict[str, Any] | None
    loader_snapshot: dict[str, Any] | None

    reserved_env_keys: dict[str, str | None]

    cache_matches_params: bool | None
    has_valid_cache: bool | None

    error: str | None


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

    # --------------------------------------------------------------------------
    # Internal helpers
    # --------------------------------------------------------------------------
    @staticmethod
    def _safe_get_ready_state() -> tuple[bool, Any, str | None]:
        try:
            state = ReadyStateCache.get()
            fingerprint = ReadyStateCache.get_fingerprint()

            if state is None or fingerprint is None:
                return False, None, None

            return True, state, fingerprint
        except Exception:
            return False, None, None

    @staticmethod
    def _safe_get_loader_snapshot() -> (
        tuple[dict[str, Any] | None, bool | None, bool | None]
    ):
        try:
            snapshot = CONFIG_STATE.snapshot()

            cache_matches = CONFIG_STATE.cache_matches_params(
                root_param=snapshot.get("root_param"),
                env_file_param=snapshot.get("env_file_param"),
            )

            has_valid_cache = CONFIG_STATE.has_valid_cache(
                root_param=snapshot.get("root_param"),
                env_file_param=snapshot.get("env_file_param"),
            )

            return snapshot, cache_matches, has_valid_cache

        except Exception:
            return None, None, None

    @staticmethod
    def _safe_get_reserved_env() -> dict[str, str | None]:
        try:
            env = get_frozen_env()
        except Exception:
            return {key: None for key in RESERVED_ENV_KEYS}

        return {key: env.get(key) for key in RESERVED_ENV_KEYS}

    # --------------------------------------------------------------------------
    # Public API
    # --------------------------------------------------------------------------
    @staticmethod
    def get_snapshot() -> ConfigDiagnosticsSnapshot:
        """
        Produce a complete, immutable diagnostics snapshot.
        NEVER raises.
        """

        ready, ready_state, fingerprint = (
            ConfigDiagnosticsProvider._safe_get_ready_state()
        )

        loader_snapshot, cache_matches, has_valid_cache = (
            ConfigDiagnosticsProvider._safe_get_loader_snapshot()
        )

        reserved_env = ConfigDiagnosticsProvider._safe_get_reserved_env()

        error = None if ready else "configuration_not_ready"

        return ConfigDiagnosticsSnapshot(
            schema_version=FSM_SCHEMA_VERSION,
            ready=ready,
            fingerprint=fingerprint,
            ready_state=(
                {
                    "status": ready_state.status.value,
                    "env": ready_state.env,
                    "settings": ready_state.settings,
                    "metadata": ready_state.metadata,
                }
                if ready_state is not None
                else None
            ),
            loader_snapshot=loader_snapshot,
            reserved_env_keys=reserved_env,
            cache_matches_params=cache_matches,
            has_valid_cache=has_valid_cache,
            error=error,
        )
