from collections.abc import Sequence

from quantum.application.decision.commands.authorize_trading_decision_command import (
    AuthorizeTradingDecisionCommand,
)
from quantum.application.decision.results.trading_decision_command_result import (
    TradingDecisionAuthorizationCommandResult,
)
from quantum.application.ports.outbound.repositories.decision_policy_repository import (
    DecisionPolicyRepository,
)
from quantum.application.ports.outbound.repositories.strategy_lifecycle_repository import (
    StrategyLifecycleRepository,
)
from quantum.application.ports.outbound.time.clock import Clock
from quantum.application.shared.base_handlers.aggregate_command_handler import (
    AggregateCommandHandler,
)
from quantum.application.shared.errors.application_error import (
    ApplicationInvariantViolation,
    NotFoundError,
)
from quantum.application.shared.eventing.application_event_context import (
    ApplicationEventContext,
)
from quantum.domain.decision.authorization.decision_authorization_status import (
    DecisionAuthorizationStatus,
)
from quantum.domain.decision.trading_decision.aggregate import TradingDecision
from quantum.domain.decision.trading_decision.events.trading_decision_authorized_event import (
    TradingDecisionAuthorizedEvent,
)
from quantum.domain.decision.trading_decision.events.trading_decision_rejected_event import (
    TradingDecisionRejectedEvent,
)
from quantum.domain.decision.trading_decision.states.trading_decision_state_base import (
    TradingDecisionStateBase,
)
from quantum.domain.shared_kernel.event_sourcing.events.base_event import BaseEvent
from quantum.domain.shared_kernel.modeling.identity.decision_id import DecisionId


class AuthorizeTradingDecisionHandler(
    AggregateCommandHandler[
        AuthorizeTradingDecisionCommand,
        TradingDecisionAuthorizationCommandResult,
        DecisionId,
        TradingDecisionStateBase,
        TradingDecision,
    ]
):
    """
    Use case: authorize or reject a trade-candidate TradingDecision.

    Existence policy expected at wiring:
    - MUST_EXIST

    Application responsibilities:
    - load governance reference data;
    - provide deterministic time;
    - delegate lifecycle/policy evaluation to the aggregate.
    """

    __slots__ = (
        "_decision_policies",
        "_strategy_lifecycles",
        "_clock",
    )

    def __init__(
        self,
        *,
        decision_policies: DecisionPolicyRepository,
        strategy_lifecycles: StrategyLifecycleRepository,
        clock: Clock,
        **base_dependencies: object,
    ) -> None:
        super().__init__(**base_dependencies)
        self._decision_policies = decision_policies
        self._strategy_lifecycles = strategy_lifecycles
        self._clock = clock

    def _aggregate_id(self, command: AuthorizeTradingDecisionCommand) -> DecisionId:
        return command.decision_id

    def _context(
        self,
        command: AuthorizeTradingDecisionCommand,
    ) -> ApplicationEventContext:
        return command.context

    def _execute_domain(
        self,
        *,
        command: AuthorizeTradingDecisionCommand,
        aggregate: TradingDecision,
    ) -> tuple[Sequence[BaseEvent], TradingDecisionAuthorizationCommandResult]:
        strategy_id = aggregate.decision_qualification().strategy_id

        policy = self._decision_policies.get_policies_for(strategy_id)
        if policy is None:
            raise NotFoundError(f"No DecisionPolicy found for strategy '{strategy_id}'")

        lifecycle = self._strategy_lifecycles.get_lifecycle(strategy_id)
        if lifecycle is None:
            raise NotFoundError(
                f"No StrategyLifecycle found for strategy '{strategy_id}'"
            )

        events = list(
            aggregate.authorize(
                policy=policy,
                lifecycle=lifecycle,
                evaluated_at=self._clock.now_epoch_ms(),
            )
        )

        if len(events) != 1:
            raise ApplicationInvariantViolation(
                "TradingDecision.authorize() must emit exactly one terminal event; "
                f"got {len(events)} event(s)"
            )

        event = events[0]

        if isinstance(event, TradingDecisionAuthorizedEvent):
            return events, TradingDecisionAuthorizationCommandResult(
                decision_id=command.decision_id,
                status=DecisionAuthorizationStatus.authorized(),
                reason_code=None,
            )

        if isinstance(event, TradingDecisionRejectedEvent):
            return events, TradingDecisionAuthorizationCommandResult(
                decision_id=command.decision_id,
                status=DecisionAuthorizationStatus.rejected(),
                reason_code=event.reason_code,
            )

        raise ApplicationInvariantViolation(
            "TradingDecision.authorize() emitted an unsupported terminal event type: "
            f"{type(event).__name__}"
        )
