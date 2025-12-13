from __future__ import annotations

from enum import Enum


class RuntimeState(Enum):
    STOPPED = "stopped"
    STARTING = "starting"
    RUNNING = "running"
    STOPPING = "stopping"


class RuntimeLifecycleViolation(RuntimeError):
    """
    Raised when the RuntimeEngine attempts an illegal state transition.
    """


class RuntimeLifecycleStateMachine:
    """
    Deterministic, minimal, certifiable runtime lifecycle FSM.

    Responsibilities:
        - Maintain the engine’s authoritative lifecycle state.
        - Enforce legal transitions (STOPPED → STARTING → RUNNING → STOPPING → STOPPED).
        - Reject illegal transitions with RuntimeLifecycleViolation.
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

    def can_transition(self, new_state: RuntimeState) -> bool:
        return new_state in self._ALLOWED.get(self._state, frozenset())

    def transition(self, new_state: RuntimeState) -> None:
        if not self.can_transition(new_state):
            raise RuntimeLifecycleViolation(
                f"Illegal state transition: {self._state.value} → {new_state.value}"
            )
        self._state = new_state

    def force_stop(self) -> None:
        """
        Force the FSM into STOPPED state.

        This method is ONLY intended for shutdown finalization when:
        - partial startup occurred
        - an unexpected exception disrupted the normal lifecycle

        This preserves global system safety and convergence guarantees.
        """
        self._state = RuntimeState.STOPPED
