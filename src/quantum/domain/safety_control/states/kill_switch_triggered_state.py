from dataclasses import dataclass

from quantum.domain.safety_control.detail import KillSwitchDetail
from quantum.domain.safety_control.reason import KillSwitchReason
from quantum.domain.safety_control.states.kill_switch_state_base import (
    KillSwitchStateBase,
)
from quantum.domain.shared_kernel.foundation.errors.invariants import InvariantViolation


@dataclass(frozen=True, slots=True)
class KillSwitchTriggeredState(KillSwitchStateBase):
    reason: KillSwitchReason
    detail: KillSwitchDetail | None = None

    def _validate_semantics(self) -> None:
        super()._validate_semantics()

        if not isinstance(self.reason, KillSwitchReason):
            raise InvariantViolation("KillSwitchTriggeredState requires reason")

        if self.detail is not None and not isinstance(self.detail, KillSwitchDetail):
            raise InvariantViolation("KillSwitchTriggeredState.detail invalid")

        if self.last_sequence.is_initial():
            raise InvariantViolation("Triggered KillSwitch cannot be initial")
