from dataclasses import dataclass

from quantum.application.shared.commands.base_command import BaseCommand
from quantum.domain.risk_governance.risk_governance_id import RiskGovernanceId
from quantum.domain.shared_kernel.modeling.monetary.pnl import RealizedPnL


@dataclass(frozen=True, slots=True)
class RegisterRealizedPnLCommand(BaseCommand):
    """
    Command: register realized PnL into an initialized RiskGovernance aggregate.
    """

    risk_governance_id: RiskGovernanceId
    pnl: RealizedPnL
