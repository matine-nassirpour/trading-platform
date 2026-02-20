from dataclasses import dataclass

from quantum.domain.risk.governance.aggregates.risk_state_base import RiskStateBase
from quantum.domain.shared_kernel.errors.invariants import InvariantViolation


@dataclass(frozen=True, slots=True)
class RiskUninitializedState(RiskStateBase):

    def _validate(self):
        if not self.last_sequence.is_initial():
            raise InvariantViolation("Uninitialized position must be initial")
