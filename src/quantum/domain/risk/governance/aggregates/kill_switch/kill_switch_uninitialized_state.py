from dataclasses import dataclass

from quantum.domain.risk.governance.aggregates.kill_switch.kill_switch_state_base import (
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
