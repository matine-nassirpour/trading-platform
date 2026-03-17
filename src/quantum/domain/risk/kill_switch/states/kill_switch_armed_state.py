from dataclasses import dataclass

from quantum.domain.risk.kill_switch.states.kill_switch_state_base import (
    KillSwitchStateBase,
)
from quantum.domain.shared_kernel.errors.invariants import InvariantViolation


@dataclass(frozen=True, slots=True)
class KillSwitchArmedState(KillSwitchStateBase):

    def _validate(self) -> None:
        super()._validate()

        if self.last_sequence.is_initial():
            raise InvariantViolation("Armed KillSwitch cannot be initial")
