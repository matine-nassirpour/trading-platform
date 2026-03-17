from dataclasses import dataclass

from quantum.domain.risk.kill_switch.reason import KillSwitchReason
from quantum.domain.risk.kill_switch.states.kill_switch_state_base import (
    KillSwitchStateBase,
)
from quantum.domain.shared_kernel.errors.invariants import InvariantViolation


@dataclass(frozen=True, slots=True)
class KillSwitchTriggeredState(KillSwitchStateBase):

    reason: KillSwitchReason

    def _validate(self) -> None:
        super()._validate()

        if not isinstance(self.reason, KillSwitchReason):
            raise InvariantViolation("KillSwitchTriggeredState requires reason")

        if self.last_sequence.is_initial():
            raise InvariantViolation("Triggered KillSwitch cannot be initial")
