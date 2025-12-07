from runtime.control_plane.diagnostic_providers.time_provider_dependency import (
    TimeProviderDependency,
)

from quantum.infrastructure.config.runtime.fsm.model import FSM_SCHEMA_VERSION
from quantum.infrastructure.config.runtime.state.config_state import CONFIG_STATE
from quantum.infrastructure.config.runtime.state.ready_cache import ReadyStateCache


class ConfigReadinessProvider:
    """
    Responsibility: Extract READY state snapshot.
    Pure read-only adapter. No JSON, no HTTP.
    """

    @staticmethod
    def get_ready_state() -> dict | None:
        time_provider = TimeProviderDependency.get()

        state = ReadyStateCache.get()
        fp = ReadyStateCache.get_fingerprint()

        if state is None or fp is None:
            return None

        return {
            "schema_version": FSM_SCHEMA_VERSION,
            "fingerprint": fp,
            "timestamp_utc": time_provider.now_utc().isoformat(),
            "ready_state": {
                "status": state.status.value,
                "env": state.env,
                "settings": state.settings,
                "metadata": state.metadata,
            },
            "runtime_snapshot": CONFIG_STATE.snapshot(),
        }
