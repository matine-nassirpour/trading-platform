from datetime import UTC, datetime

from quantum.infrastructure.config.runtime.fsm.model import FSM_SCHEMA_VERSION
from quantum.infrastructure.config.runtime.state.config_state import CONFIG_STATE
from quantum.infrastructure.config.runtime.state.ready_cache import ReadyStateCache


class ReadyStateAdapter:
    """
    Responsibility: Extract READY state snapshot.
    Pure read-only adapter. No JSON, no HTTP.
    """

    @staticmethod
    def get_ready_state() -> dict | None:
        state = ReadyStateCache.get()
        fp = ReadyStateCache.get_fingerprint()

        if state is None or fp is None:
            return None

        return {
            "schema_version": FSM_SCHEMA_VERSION,
            "fingerprint": fp,
            "timestamp_utc": datetime.now(UTC).isoformat(),
            "ready_state": {
                "env": state.env,
                "settings": state.settings,
                "metadata": state.metadata,
            },
            "runtime_snapshot": CONFIG_STATE.snapshot(),
        }
