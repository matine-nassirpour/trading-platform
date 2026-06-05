from collections.abc import Sequence

from quantum.application.risk_governance.commands.register_realized_pnl_command import (
    RegisterRealizedPnLCommand,
)
from quantum.application.risk_governance.results.risk_governance_command_result import (
    RegisterRealizedPnLResult,
)
from quantum.application.shared.base_handlers.aggregate_command_handler import (
    AggregateCommandHandler,
)
from quantum.application.shared.eventing.application_event_context import (
    ApplicationEventContext,
)
from quantum.domain.risk_governance.aggregate import RiskGovernance
from quantum.domain.risk_governance.lifecycle.states.risk_governance_state_base import (
    RiskGovernanceStateBase,
)
from quantum.domain.risk_governance.risk_governance_id import RiskGovernanceId
from quantum.domain.shared_kernel.event_sourcing.events.base_event import BaseEvent


class RegisterRealizedPnLHandler(
    AggregateCommandHandler[
        RegisterRealizedPnLCommand,
        RegisterRealizedPnLResult,
        RiskGovernanceId,
        RiskGovernanceStateBase,
        RiskGovernance,
    ]
):
    """
    Use case: register realized PnL and delegate all risk evolution to the domain.

    Existence policy expected at composition root:
    - MUST_EXIST
    """

    def _aggregate_id(
        self,
        command: RegisterRealizedPnLCommand,
    ) -> RiskGovernanceId:
        return command.risk_governance_id

    def _context(
        self,
        command: RegisterRealizedPnLCommand,
    ) -> ApplicationEventContext:
        return command.context

    async def _execute_domain(
        self,
        *,
        command: RegisterRealizedPnLCommand,
        aggregate: RiskGovernance,
    ) -> tuple[Sequence[BaseEvent], RegisterRealizedPnLResult]:
        outcome, events = aggregate.register_pnl(pnl=command.pnl)

        return events, RegisterRealizedPnLResult(
            risk_governance_id=command.risk_governance_id,
            resulting_snapshot=outcome.resulting_snapshot,
            active_breaches=outcome.active_breaches,
            insolvency_declared=outcome.insolvency_declared,
        )
