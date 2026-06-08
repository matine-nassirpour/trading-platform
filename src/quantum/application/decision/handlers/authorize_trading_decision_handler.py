from collections.abc import Sequence

from quantum.application.decision.commands.authorize_trading_decision_command import (
    AuthorizeTradingDecisionCommand,
)
from quantum.application.decision.results.trading_decision_command_result import (
    TradingDecisionAuthorizationCommandResult,
)
from quantum.application.ports.outbound.repositories.decision_policy_provider import (
    DecisionPolicyProvider,
)
from quantum.application.ports.outbound.repositories.strategy_lifecycle_provider import (
    StrategyLifecycleProvider,
)
from quantum.application.ports.outbound.time.clock import Clock
from quantum.application.ports.outbound.transaction.unit_of_work_factory import (
    UnitOfWorkFactory,
)
from quantum.application.shared.base_handlers.aggregate_command_handler import (
    AggregateCommandHandler,
)
from quantum.application.shared.base_handlers.aggregate_existence_policy import (
    AggregateExistencePolicy,
)
from quantum.application.shared.base_handlers.domain_event_batch_policy import (
    DomainEventBatchPolicy,
)
from quantum.application.shared.base_handlers.empty_event_policy import EmptyEventPolicy
from quantum.application.shared.errors.application_error import (
    ApplicationInvariantViolationError,
    NotFoundError,
)
from quantum.application.shared.eventing.application_event_context import (
    ApplicationEventContext,
)
from quantum.application.shared.eventing.event_enveloper import (
    ApplicationEventEnveloper,
)
from quantum.application.shared.eventing.stream_name_resolver import StreamNameResolver
from quantum.domain.decision.trading_decision.aggregate import TradingDecision
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
        decision_policies: DecisionPolicyProvider,
        strategy_lifecycles: StrategyLifecycleProvider,
        clock: Clock,
        aggregate_type: type[TradingDecision],
        stream_resolver: StreamNameResolver[DecisionId],
        uow_factory: UnitOfWorkFactory,
        enveloper: ApplicationEventEnveloper,
        existence_policy: AggregateExistencePolicy,
        empty_event_policy: EmptyEventPolicy = EmptyEventPolicy.FORBID,
        event_batch_policy: DomainEventBatchPolicy | None = None,
    ) -> None:
        super().__init__(
            aggregate_type=aggregate_type,
            stream_resolver=stream_resolver,
            uow_factory=uow_factory,
            enveloper=enveloper,
            existence_policy=existence_policy,
            empty_event_policy=empty_event_policy,
            event_batch_policy=event_batch_policy,
        )
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

    async def _execute_domain(
        self,
        *,
        command: AuthorizeTradingDecisionCommand,
        aggregate: TradingDecision,
    ) -> tuple[Sequence[BaseEvent], TradingDecisionAuthorizationCommandResult]:
        strategy_id = aggregate.decision_qualification().strategy_id

        policy = await self._decision_policies.get_policies_for(strategy_id)
        if policy is None:
            raise NotFoundError(f"No DecisionPolicy found for strategy '{strategy_id}'")

        lifecycle = await self._strategy_lifecycles.get_lifecycle(strategy_id)
        if lifecycle is None:
            raise NotFoundError(
                f"No StrategyLifecycle found for strategy '{strategy_id}'"
            )

        evaluated_at = await self._clock.now_epoch_ms()

        outcome, events = aggregate.authorize(
            policy=policy,
            lifecycle=lifecycle,
            evaluated_at=evaluated_at,
        )

        if len(events) != 1:
            raise ApplicationInvariantViolationError(
                "TradingDecision.authorize() must emit exactly one terminal event; "
                f"got {len(events)} event(s)"
            )

        return events, TradingDecisionAuthorizationCommandResult(
            decision_id=command.decision_id,
            status=outcome.status,
            reason_code=outcome.reason_code,
        )
