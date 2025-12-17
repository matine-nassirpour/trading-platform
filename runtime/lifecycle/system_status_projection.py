from runtime.admin.contracts.system_status import SystemStatus
from runtime.lifecycle.state_machine import RuntimeState


def system_status_from_runtime_state(state: RuntimeState) -> SystemStatus:
    """
    Project the internal runtime lifecycle state
    into a stable, external SystemStatus.

    Mapping:
        RUNNING   → UP
        STARTING  → DEGRADED
        STOPPING  → DEGRADED
        STOPPED   → DOWN
    """
    if state is RuntimeState.RUNNING:
        return SystemStatus.UP

    if state in (RuntimeState.STARTING, RuntimeState.STOPPING):
        return SystemStatus.DEGRADED

    return SystemStatus.DOWN
