from __future__ import annotations

from enum import Enum


class RuntimeState(Enum):
    STOPPED = "stopped"
    STARTING = "starting"
    RUNNING = "running"
    STOPPING = "stopping"


class RuntimeInvalidStateError(RuntimeError):
    """
    Raised when the RuntimeEngine attempts an illegal state transition.
    """


class RuntimeStateMachine:
    """
    Deterministic, minimal, certifiable runtime lifecycle FSM.

    Responsibilities:
        - Maintain the engine’s authoritative lifecycle state.
        - Enforce legal transitions (STOPPED → STARTING → RUNNING → STOPPING → STOPPED).
        - Reject illegal transitions with RuntimeInvalidStateError.
        - Provide a strictly pure, side-effect-free API.
    """

    _ALLOWED: dict[RuntimeState, frozenset[RuntimeState]] = {
        RuntimeState.STOPPED: frozenset({RuntimeState.STARTING}),
        RuntimeState.STARTING: frozenset({RuntimeState.RUNNING, RuntimeState.STOPPING}),
        RuntimeState.RUNNING: frozenset({RuntimeState.STOPPING}),
        RuntimeState.STOPPING: frozenset({RuntimeState.STOPPED}),
    }

    def __init__(self) -> None:
        self._state = RuntimeState.STOPPED

    @property
    def state(self) -> RuntimeState:
        return self._state

    def transition(self, new_state: RuntimeState) -> None:
        allowed = self._ALLOWED.get(self._state, frozenset())

        if new_state not in allowed:
            raise RuntimeInvalidStateError(
                f"Illegal state transition: {self._state.value} → {new_state.value}"
            )

        self._state = new_state
