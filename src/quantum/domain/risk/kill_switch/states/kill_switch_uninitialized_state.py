from dataclasses import dataclass

from quantum.domain.risk.kill_switch.states.kill_switch_state_base import (
    KillSwitchStateBase,
)
from quantum.domain.shared_kernel.errors.invariants import InvariantViolation


@dataclass(frozen=True, slots=True)
class KillSwitchUninitializedState(KillSwitchStateBase):

    def _validate(self) -> None:
        if not self.last_sequence.is_initial():
            raise InvariantViolation(
                "Uninitialized KillSwitch must have initial sequence"
            )
