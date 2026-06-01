from collections.abc import Sequence

from quantum.application.risk_governance.commands.initialize_risk_governance_command import (
    InitializeRiskGovernanceCommand,
)
from quantum.application.risk_governance.results.risk_governance_command_result import (
    InitializeRiskGovernanceResult,
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


class InitializeRiskGovernanceHandler(
    AggregateCommandHandler[
        InitializeRiskGovernanceCommand,
        InitializeRiskGovernanceResult,
        RiskGovernanceId,
        RiskGovernanceStateBase,
        RiskGovernance,
    ]
):
    """
    Use case: initialize one RiskGovernance aggregate.

    Existence policy expected at composition root:
    - MUST_NOT_EXIST
    """

    def _aggregate_id(
        self,
        command: InitializeRiskGovernanceCommand,
    ) -> RiskGovernanceId:
        return command.risk_governance_id

    def _context(
        self,
        command: InitializeRiskGovernanceCommand,
    ) -> ApplicationEventContext:
        return command.context

    def _execute_domain(
        self,
        *,
        command: InitializeRiskGovernanceCommand,
        aggregate: RiskGovernance,
    ) -> tuple[Sequence[BaseEvent], InitializeRiskGovernanceResult]:
        events = RiskGovernance.initialize(
            limits=command.limits,
            initial_snapshot=command.initial_snapshot,
            trading_day=command.trading_day,
        )

        return events, InitializeRiskGovernanceResult(
            risk_governance_id=command.risk_governance_id,
        )
