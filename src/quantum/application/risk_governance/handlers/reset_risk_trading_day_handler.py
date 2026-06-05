from collections.abc import Sequence

from quantum.application.risk_governance.commands.reset_risk_trading_day_command import (
    ResetRiskTradingDayCommand,
)
from quantum.application.risk_governance.results.risk_governance_command_result import (
    ResetRiskTradingDayResult,
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


class ResetRiskTradingDayHandler(
    AggregateCommandHandler[
        ResetRiskTradingDayCommand,
        ResetRiskTradingDayResult,
        RiskGovernanceId,
        RiskGovernanceStateBase,
        RiskGovernance,
    ]
):
    """
    Use case: reset daily risk counters for a new trading day.

    Existence policy expected at composition root:
    - MUST_EXIST
    """

    def _aggregate_id(
        self,
        command: ResetRiskTradingDayCommand,
    ) -> RiskGovernanceId:
        return command.risk_governance_id

    def _context(
        self,
        command: ResetRiskTradingDayCommand,
    ) -> ApplicationEventContext:
        return command.context

    async def _execute_domain(
        self,
        *,
        command: ResetRiskTradingDayCommand,
        aggregate: RiskGovernance,
    ) -> tuple[Sequence[BaseEvent], ResetRiskTradingDayResult]:
        events = aggregate.reset_trading_day(trading_day=command.trading_day)

        return events, ResetRiskTradingDayResult(
            risk_governance_id=command.risk_governance_id,
            event_emitted=bool(events),
        )
