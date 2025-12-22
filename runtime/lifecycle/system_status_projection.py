from runtime.control_plane.contracts.system_status import SystemStatus
from runtime.lifecycle.state_machine import RuntimeState


def system_status_from_runtime_state(state: RuntimeState) -> SystemStatus:
    """
    Project the internal runtime lifecycle state
    into the external contractual SystemStatus.

    This function is:
    - deterministic
    - total (covers all states)
    - contract-aligned
    """
    if state is RuntimeState.RUNNING:
        return SystemStatus.UP

    if state in (RuntimeState.STARTING, RuntimeState.STOPPING):
        return SystemStatus.DEGRADED

    return SystemStatus.DOWN
