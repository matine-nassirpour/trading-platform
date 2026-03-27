from collections.abc import Mapping
from typing import Self

from quantum.domain.decision.authorization.decision_authorization_result import (
    DecisionAuthorizationResult,
)
from quantum.domain.decision.authorization.decision_policy import DecisionPolicy
from quantum.domain.decision.authorization.decision_policy_evaluator import (
    DecisionPolicyEvaluator,
)
from quantum.domain.decision.authorization.strategy_eligibility_policy import (
    StrategyEligibilityPolicy,
)
from quantum.domain.decision.authorization.strategy_lifecycle import StrategyLifecycle
from quantum.domain.decision.common.trading_context import TradingContext
from quantum.domain.decision.no_trade.no_trade_decision import NoTradeDecision
from quantum.domain.decision.qualification.decision_identity import DecisionIdentity
from quantum.domain.decision.trading_decision.events.trading_decision_authorized_event import (
    TradingDecisionAuthorizedEvent,
)
from quantum.domain.decision.trading_decision.events.trading_decision_created_event import (
    TradingDecisionCreatedEvent,
)
from quantum.domain.decision.trading_decision.events.trading_decision_evaluated_as_no_trade_event import (
    TradingDecisionEvaluatedAsNoTradeEvent,
)
from quantum.domain.decision.trading_decision.events.trading_decision_evaluated_as_trade_candidate_event import (
    TradingDecisionEvaluatedAsTradeCandidateEvent,
)
from quantum.domain.decision.trading_decision.events.trading_decision_rejected_event import (
    TradingDecisionRejectedEvent,
)
from quantum.domain.decision.trading_decision.states.trading_decision_authorized_state import (
    TradingDecisionAuthorizedState,
)
from quantum.domain.decision.trading_decision.states.trading_decision_no_trade_state import (
    TradingDecisionNoTradeState,
)
from quantum.domain.decision.trading_decision.states.trading_decision_pending_evaluation_state import (
    TradingDecisionPendingEvaluationState,
)
from quantum.domain.decision.trading_decision.states.trading_decision_rejected_state import (
    TradingDecisionRejectedState,
)
from quantum.domain.decision.trading_decision.states.trading_decision_state_base import (
    TradingDecisionStateBase,
)
from quantum.domain.decision.trading_decision.states.trading_decision_trade_candidate_pending_authorization_state import (
    TradingDecisionTradeCandidatePendingAuthorizationState,
)
from quantum.domain.decision.trading_decision.states.trading_decision_uninitialized_state import (
    TradingDecisionUninitializedState,
)
from quantum.domain.market.instrument.identity.symbol import Symbol
from quantum.domain.market.positioning.position_side import PositionSide
from quantum.domain.shared_kernel.event_sourcing.aggregates.event_sourced_aggregate_root import (
    EventHandler,
    EventSourcedAggregateRoot,
)
from quantum.domain.shared_kernel.event_sourcing.events.base_event import BaseEvent
from quantum.domain.shared_kernel.event_sourcing.events.event_sequence import (
    EventSequence,
)
from quantum.domain.shared_kernel.event_sourcing.events.recorded_event_envelope import (
    RecordedEventEnvelope,
)
from quantum.domain.shared_kernel.foundation.errors.invariants import (
    InvalidStateTransition,
    InvariantViolation,
)
from quantum.domain.shared_kernel.modeling.identity.decision_id import DecisionId
from quantum.domain.shared_kernel.modeling.temporal.epoch_ms import EpochMs


class TradingDecision(EventSourcedAggregateRoot[DecisionId, TradingDecisionStateBase]):
    """
    TradingDecision — canonical decision aggregate.

    Responsibilities:
    - represent one auditable trading decision flow
    - capture decision identity and market context
    - resolve the decision to exactly one evaluation outcome:
        * trade candidate
        * no trade
    - authorize or reject a trade candidate
    - preserve strict mutual exclusivity of terminal outcomes

    Explicitly DOES NOT:
    - reserve capital
    - size positions
    - create broker orders
    - know execution infrastructure
    """

    __slots__ = ()

    @classmethod
    def aggregate_id_type(cls) -> type[DecisionId]:
        return DecisionId

    @classmethod
    def state_type(cls) -> type[TradingDecisionStateBase]:
        return TradingDecisionStateBase

    @classmethod
    def uninitialized_state(cls) -> TradingDecisionStateBase:
        return TradingDecisionUninitializedState(
            last_sequence=EventSequence.initial(),
        )

    # --- Internal state guards ------------------------------------------------

    def _require_pending_evaluation(self) -> TradingDecisionPendingEvaluationState:
        state = self.state

        if not isinstance(state, TradingDecisionPendingEvaluationState):
            raise InvalidStateTransition("TradingDecision is not pending evaluation")

        return state

    def _require_trade_candidate_pending_authorization(
        self,
    ) -> TradingDecisionTradeCandidatePendingAuthorizationState:
        state = self.state

        if not isinstance(
            state,
            TradingDecisionTradeCandidatePendingAuthorizationState,
        ):
            raise InvalidStateTransition(
                "TradingDecision is not a trade candidate awaiting authorization"
            )

        return state

    # --- Creation API ---------------------------------------------------------

    @classmethod
    def decide_create(
        cls,
        *,
        symbol: Symbol,
        decision_identity: DecisionIdentity,
        context: TradingContext,
    ) -> list[BaseEvent]:
        """
        Pure domain decision for creating a new TradingDecision.
        """

        return [
            TradingDecisionCreatedEvent(
                symbol=symbol,
                decision_identity=decision_identity,
                trading_context=context,
            )
        ]

    @classmethod
    def create_new(
        cls,
        *,
        aggregate_id: DecisionId,
        symbol: Symbol,
        decision_identity: DecisionIdentity,
        context: TradingContext,
    ) -> tuple[Self, list[BaseEvent]]:
        """
        Canonical factory for a brand-new TradingDecision aggregate.

        The returned aggregate remains empty until the recorded creation event
        is persisted and applied.
        """

        aggregate = cls.new(aggregate_id=aggregate_id)

        domain_events = cls.decide_create(
            symbol=symbol,
            decision_identity=decision_identity,
            context=context,
        )

        return aggregate, domain_events

    # --- Commands -------------------------------------------------------------

    def evaluate_as_trade_candidate(
        self,
        *,
        side: PositionSide,
    ) -> list[BaseEvent]:
        """
        Resolves a pending decision into a trade candidate.
        """

        self._require_pending_evaluation()

        return [
            TradingDecisionEvaluatedAsTradeCandidateEvent(
                side=side,
            )
        ]

    def evaluate_as_no_trade(
        self,
        *,
        no_trade_decision: NoTradeDecision,
    ) -> list[BaseEvent]:
        """
        Resolves a pending decision into an explicit NO-TRADE outcome.
        """

        self._require_pending_evaluation()

        return [
            TradingDecisionEvaluatedAsNoTradeEvent(
                no_trade_decision=no_trade_decision,
            )
        ]

    def authorize(
        self,
        *,
        policy: DecisionPolicy,
        lifecycle: StrategyLifecycle,
        evaluated_at: EpochMs,
    ) -> list[BaseEvent]:
        """
        Evaluates a trade candidate against lifecycle and governance policy.

        Valid only after the decision has already been resolved as a trade
        candidate.
        """

        state = self._require_trade_candidate_pending_authorization()

        lifecycle_result = StrategyEligibilityPolicy.evaluate(
            decision=state.decision_identity,
            lifecycle=lifecycle,
            at=evaluated_at,
        )

        if lifecycle_result.is_rejected():
            return [
                TradingDecisionRejectedEvent(
                    reason_code=lifecycle_result.reason_code,
                )
            ]

        policy_result = DecisionPolicyEvaluator.evaluate(
            policy=policy,
            decision=state.decision_identity,
            context=state.context,
            at=evaluated_at,
        )

        if policy_result.is_rejected():
            return [
                TradingDecisionRejectedEvent(
                    reason_code=policy_result.reason_code,
                )
            ]

        return [
            TradingDecisionAuthorizedEvent(),
        ]

    # --- Event → State transitions --------------------------------------------

    @staticmethod
    def _apply_created(
        state: TradingDecisionStateBase,
        event: BaseEvent,
        envelope: RecordedEventEnvelope,
    ) -> TradingDecisionStateBase:

        if not isinstance(state, TradingDecisionUninitializedState):
            raise InvariantViolation("TradingDecision already exists")

        if not isinstance(event, TradingDecisionCreatedEvent):
            raise InvariantViolation(
                "TradingDecision._apply_created requires TradingDecisionCreatedEvent"
            )

        return TradingDecisionPendingEvaluationState(
            last_sequence=envelope.sequence,
            symbol=event.symbol,
            decision_identity=event.decision_identity,
            context=event.trading_context,
        )

    @staticmethod
    def _apply_evaluated_as_trade_candidate(
        state: TradingDecisionStateBase,
        event: BaseEvent,
        envelope: RecordedEventEnvelope,
    ) -> TradingDecisionStateBase:

        if not isinstance(state, TradingDecisionPendingEvaluationState):
            raise InvariantViolation(
                "TradingDecision must be pending evaluation to become a trade candidate"
            )

        if not isinstance(event, TradingDecisionEvaluatedAsTradeCandidateEvent):
            raise InvariantViolation(
                "TradingDecision._apply_evaluated_as_trade_candidate requires "
                "TradingDecisionEvaluatedAsTradeCandidateEvent"
            )

        return TradingDecisionTradeCandidatePendingAuthorizationState(
            last_sequence=envelope.sequence,
            symbol=state.symbol,
            side=event.side,
            decision_identity=state.decision_identity,
            context=state.context,
        )

    @staticmethod
    def _apply_evaluated_as_no_trade(
        state: TradingDecisionStateBase,
        event: BaseEvent,
        envelope: RecordedEventEnvelope,
    ) -> TradingDecisionStateBase:

        if not isinstance(state, TradingDecisionPendingEvaluationState):
            raise InvariantViolation(
                "TradingDecision must be pending evaluation to become a no-trade decision"
            )

        if not isinstance(event, TradingDecisionEvaluatedAsNoTradeEvent):
            raise InvariantViolation(
                "TradingDecision._apply_evaluated_as_no_trade requires "
                "TradingDecisionEvaluatedAsNoTradeEvent"
            )

        return TradingDecisionNoTradeState(
            last_sequence=envelope.sequence,
            symbol=state.symbol,
            decision_identity=state.decision_identity,
            context=state.context,
            no_trade_decision=event.no_trade_decision,
        )

    @staticmethod
    def _apply_authorized(
        state: TradingDecisionStateBase,
        event: BaseEvent,
        envelope: RecordedEventEnvelope,
    ) -> TradingDecisionStateBase:

        if not isinstance(
            state,
            TradingDecisionTradeCandidatePendingAuthorizationState,
        ):
            raise InvariantViolation(
                "TradingDecision must be awaiting authorization to become authorized"
            )

        if not isinstance(event, TradingDecisionAuthorizedEvent):
            raise InvariantViolation(
                "TradingDecision._apply_authorized requires TradingDecisionAuthorizedEvent"
            )

        return TradingDecisionAuthorizedState(
            last_sequence=envelope.sequence,
            symbol=state.symbol,
            side=state.side,
            decision_identity=state.decision_identity,
            context=state.context,
            authorization_result=DecisionAuthorizationResult.authorized(),
        )

    @staticmethod
    def _apply_rejected(
        state: TradingDecisionStateBase,
        event: BaseEvent,
        envelope: RecordedEventEnvelope,
    ) -> TradingDecisionStateBase:

        if not isinstance(
            state,
            TradingDecisionTradeCandidatePendingAuthorizationState,
        ):
            raise InvariantViolation(
                "TradingDecision must be awaiting authorization to become rejected"
            )

        if not isinstance(event, TradingDecisionRejectedEvent):
            raise InvariantViolation(
                "TradingDecision._apply_rejected requires TradingDecisionRejectedEvent"
            )

        return TradingDecisionRejectedState(
            last_sequence=envelope.sequence,
            symbol=state.symbol,
            side=state.side,
            decision_identity=state.decision_identity,
            context=state.context,
            authorization_result=DecisionAuthorizationResult.rejected(
                reason_code=event.reason_code
            ),
        )

    # --- Handler registry -----------------------------------------------------

    @classmethod
    def _handlers(
        cls,
    ) -> Mapping[type[BaseEvent], EventHandler[TradingDecisionStateBase, BaseEvent]]:
        return {
            TradingDecisionCreatedEvent: cls._apply_created,
            TradingDecisionEvaluatedAsTradeCandidateEvent: (
                cls._apply_evaluated_as_trade_candidate
            ),
            TradingDecisionEvaluatedAsNoTradeEvent: cls._apply_evaluated_as_no_trade,
            TradingDecisionAuthorizedEvent: cls._apply_authorized,
            TradingDecisionRejectedEvent: cls._apply_rejected,
        }
