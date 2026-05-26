from dataclasses import dataclass

from quantum.domain.safety_control.kill_switch.states.kill_switch_state_base import (
    KillSwitchStateBase,
)
from quantum.domain.shared_kernel.foundation.errors.invariants import InvariantViolation


@dataclass(frozen=True, slots=True)
class KillSwitchArmedState(KillSwitchStateBase):

    def _validate_semantics(self) -> None:
        super()._validate_semantics()

        if self.last_sequence.is_initial():
            raise InvariantViolation("Armed KillSwitch cannot be initial")
