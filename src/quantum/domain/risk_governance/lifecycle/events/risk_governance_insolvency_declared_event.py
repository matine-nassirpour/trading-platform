from dataclasses import dataclass
from typing import ClassVar

from quantum.domain.risk_governance.lifecycle.events.risk_governance_event import (
    RiskGovernanceEvent,
)
from quantum.domain.risk_governance.portfolio_state.risk_snapshot import RiskSnapshot
from quantum.domain.shared_kernel.foundation.errors.invariants import InvariantViolation


@dataclass(frozen=True, slots=True)
class RiskGovernanceInsolvencyDeclaredEvent(RiskGovernanceEvent):
    event_name: ClassVar[str] = "risk_governance.insolvency.declared"
    event_version: ClassVar[int] = 1

    snapshot: RiskSnapshot

    def _validate_payload(self) -> None:
        if not isinstance(self.snapshot, RiskSnapshot):
            raise InvariantViolation(
                "RiskGovernanceInsolvencyDeclaredEvent.snapshot must be RiskSnapshot"
            )

        if self.snapshot.equity.value > 0:
            raise InvariantViolation(
                "RiskGovernanceInsolvencyDeclaredEvent requires equity <= 0"
            )
