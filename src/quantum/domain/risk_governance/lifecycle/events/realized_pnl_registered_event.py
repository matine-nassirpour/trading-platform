from dataclasses import dataclass
from typing import ClassVar

from quantum.domain.risk_governance.lifecycle.events.risk_governance_event import (
    RiskGovernanceEvent,
)
from quantum.domain.risk_governance.portfolio_state.risk_snapshot import RiskSnapshot
from quantum.domain.shared_kernel.foundation.errors.invariants import InvariantViolation
from quantum.domain.shared_kernel.modeling.monetary.pnl import RealizedPnL


@dataclass(frozen=True, slots=True)
class RealizedPnLRegisteredEvent(RiskGovernanceEvent):
    event_name: ClassVar[str] = "risk_governance.realized_pnl.registered"
    event_version: ClassVar[int] = 1

    pnl: RealizedPnL
    resulting_snapshot: RiskSnapshot

    def _validate_payload(self) -> None:
        if not isinstance(self.pnl, RealizedPnL):
            raise InvariantViolation(
                "RealizedPnLRegisteredEvent.pnl must be RealizedPnL"
            )

        if not isinstance(self.resulting_snapshot, RiskSnapshot):
            raise InvariantViolation(
                "RealizedPnLRegisteredEvent.resulting_snapshot must be RiskSnapshot"
            )

        if self.pnl.context != self.resulting_snapshot.equity.context:
            raise InvariantViolation(
                "RealizedPnLRegisteredEvent pnl/resulting_snapshot MoneyContext mismatch"
            )

        if self.pnl.currency != self.resulting_snapshot.equity.currency:
            raise InvariantViolation(
                "RealizedPnLRegisteredEvent pnl/resulting_snapshot currency mismatch"
            )
