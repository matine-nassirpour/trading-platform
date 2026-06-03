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
from quantum.application.shared.errors.application_error import (
    ApplicationInvariantViolation,
)
from quantum.application.shared.eventing.application_event_context import (
    ApplicationEventContext,
)
from quantum.domain.risk_governance.aggregate import RiskGovernance
from quantum.domain.risk_governance.breach_detection.breaches.risk_breach import (
    RiskBreach,
)
from quantum.domain.risk_governance.lifecycle.events.realized_pnl_registered_event import (
    RealizedPnLRegisteredEvent,
)
from quantum.domain.risk_governance.lifecycle.events.risk_breaches_detected_event import (
    RiskBreachesDetectedEvent,
)
from quantum.domain.risk_governance.lifecycle.events.risk_governance_insolvency_declared_event import (
    RiskGovernanceInsolvencyDeclaredEvent,
)
from quantum.domain.risk_governance.lifecycle.states.risk_governance_state_base import (
    RiskGovernanceStateBase,
)
from quantum.domain.risk_governance.portfolio_state.risk_snapshot import RiskSnapshot
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

    # --- Internal Helpers -----------------------------------------------------

    @staticmethod
    def _extract_resulting_snapshot(events: Sequence[BaseEvent]) -> RiskSnapshot:
        for event in events:
            if isinstance(event, RealizedPnLRegisteredEvent):
                return event.resulting_snapshot

        raise ApplicationInvariantViolation(
            "RiskGovernance.register_pnl() must emit RealizedPnLRegisteredEvent"
        )

    @staticmethod
    def _extract_detected_breaches(
        events: Sequence[BaseEvent],
    ) -> tuple[RiskBreach, ...]:
        for event in events:
            if isinstance(event, RiskBreachesDetectedEvent):
                return event.breaches

        return ()

    @staticmethod
    def _contains_insolvency_declaration(events: Sequence[BaseEvent]) -> bool:
        return any(
            isinstance(event, RiskGovernanceInsolvencyDeclaredEvent) for event in events
        )

    # --- Domain Executor ------------------------------------------------------

    def _execute_domain(
        self,
        *,
        command: RegisterRealizedPnLCommand,
        aggregate: RiskGovernance,
    ) -> tuple[Sequence[BaseEvent], RegisterRealizedPnLResult]:
        events = list(aggregate.register_pnl(pnl=command.pnl))

        resulting_snapshot = self._extract_resulting_snapshot(events)
        active_breaches = self._extract_detected_breaches(events)
        insolvency_declared = self._contains_insolvency_declaration(events)

        return events, RegisterRealizedPnLResult(
            risk_governance_id=command.risk_governance_id,
            resulting_snapshot=resulting_snapshot,
            active_breaches=active_breaches,
            insolvency_declared=insolvency_declared,
        )
