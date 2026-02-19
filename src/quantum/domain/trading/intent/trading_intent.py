from collections.abc import Mapping
from dataclasses import dataclass

from quantum.domain.decision.context.trading_context import TradingContext
from quantum.domain.decision.events.v1.decision_authorized_event import (
    DecisionAuthorizedEvent,
)
from quantum.domain.decision.events.v1.decision_rejected_event import (
    DecisionRejectedEvent,
)
from quantum.domain.decision.governance.decision_authorization_result import (
    DecisionAuthorizationResult,
)
from quantum.domain.decision.governance.decision_policy import DecisionPolicy
from quantum.domain.decision.governance.decision_policy_evaluator import (
    DecisionPolicyEvaluator,
)
from quantum.domain.decision.identity.decision_identity import DecisionIdentity
from quantum.domain.risk.lifecycle.strategy_eligibility_policy import (
    StrategyEligibilityPolicy,
)
from quantum.domain.risk.lifecycle.strategy_lifecycle import StrategyLifecycle
from quantum.domain.shared_kernel.errors.invariants import (
    InvalidStateTransition,
    InvariantViolation,
)
from quantum.domain.shared_kernel.events.base.base_event import BaseEvent
from quantum.domain.shared_kernel.events.event_envelope import EventEnvelope
from quantum.domain.shared_kernel.events.event_sequence import EventSequence
from quantum.domain.shared_kernel.identifiers.intent_id import IntentId
from quantum.domain.shared_kernel.primitives.aggregate_state import AggregateState
from quantum.domain.shared_kernel.primitives.event_sourced_aggregate_root import (
    EventHandler,
    EventSourcedAggregateRoot,
)
from quantum.domain.shared_kernel.value_objects.epoch_ms import EpochMs
from quantum.domain.shared_kernel.value_objects.symbol import Symbol
from quantum.domain.trading.events.v1.intent.trading_intent_created_event import (
    TradingIntentCreatedEvent,
)
from quantum.domain.trading.execution.order.position_side import PositionSide


@dataclass(frozen=True, slots=True)
class TradingIntentState(AggregateState):
    """
    Immutable state of a TradingIntent.

    This state represents a GOVERNED DECISION,
    not an execution instruction.
    """

    last_sequence: EventSequence

    intent_id: IntentId
    symbol: Symbol
    side: PositionSide

    decision_identity: DecisionIdentity
    context: TradingContext
    authorization_result: DecisionAuthorizationResult | None

    def last_event_sequence(self) -> EventSequence:
        return self.last_sequence

    def _validate_types(self) -> None:
        if not isinstance(self.intent_id, IntentId):
            raise InvariantViolation("TradingIntent requires a valid IntentId")

        if not isinstance(self.symbol, Symbol):
            raise InvariantViolation("TradingIntent requires a Symbol")

        if not isinstance(self.side, PositionSide):
            raise InvariantViolation("TradingIntent requires a PositionSide")

        if not isinstance(self.decision_identity, DecisionIdentity):
            raise InvariantViolation("TradingIntent requires DecisionIdentity")

        if not isinstance(self.context, TradingContext):
            raise InvariantViolation("TradingIntent requires TradingContext")

    def _validate(self) -> None:
        self._validate_types()

        if self.last_sequence is None:
            raise InvariantViolation("last_sequence required")

        if self.authorization_result is not None:
            if not isinstance(self.authorization_result, DecisionAuthorizationResult):
                raise InvariantViolation("authorization_result invalid")

    def is_evaluated(self) -> bool:
        return self.authorization_result is not None

    def is_authorized(self) -> bool:
        return (
            self.authorization_result is not None
            and self.authorization_result.is_authorized()
        )

    def is_rejected(self) -> bool:
        return (
            self.authorization_result is not None
            and self.authorization_result.is_rejected()
        )


class TradingIntent(EventSourcedAggregateRoot[TradingIntentState]):
    """
    TradingIntent — Decision Aggregate (PURE DOMAIN)

    Responsibilities:
    - Represent a trading decision
    - Carry decision identity and context
    - Track authorization outcome
    - Emit governance events

    Explicitly DOES NOT:
    - create orders
    - know about execution
    - perform pricing
    - handle risk or sizing
    """

    # --- Factory --------------------------------------------------------------

    @staticmethod
    def create(
        *,
        intent_id: IntentId,
        symbol: Symbol,
        side: PositionSide,
        decision_identity: DecisionIdentity,
        context: TradingContext,
    ) -> list[BaseEvent]:
        """
        Creates a new trading intent.

        This represents:
        - a decision has been made
        - it must now be evaluated by governance
        """

        return [
            TradingIntentCreatedEvent(
                intent_id=intent_id,
                symbol=symbol,
                side=side,
                decision_identity=decision_identity,
                trading_context=context,
            )
        ]

    # --- Commands -------------------------------------------------------------

    @staticmethod
    def _evaluate_decision_authorization(
        *,
        decision: DecisionIdentity,
        context: TradingContext,
        lifecycle: StrategyLifecycle,
        policy: DecisionPolicy,
        evaluated_at: EpochMs,
    ) -> DecisionAuthorizationResult:
        lifecycle_result = StrategyEligibilityPolicy.evaluate(
            lifecycle=lifecycle,
            at=evaluated_at,
        )

        if lifecycle_result.is_rejected():
            return lifecycle_result

        policy_result = DecisionPolicyEvaluator.evaluate(
            policy=policy,
            decision=decision,
            context=context,
        )

        if policy_result.is_rejected():
            return policy_result

        return DecisionAuthorizationResult.authorized(
            reason="Decision authorized",
        )

    def evaluate(
        self,
        *,
        policy: DecisionPolicy,
        lifecycle: StrategyLifecycle,
        evaluated_at: EpochMs,
    ) -> list[BaseEvent]:

        state = self.state

        if state is None:
            raise InvalidStateTransition("TradingIntent not created")

        if state.is_evaluated():
            raise InvalidStateTransition("TradingIntent already evaluated")

        authorization = self._evaluate_decision_authorization(
            decision=state.decision_identity,
            context=state.context,
            lifecycle=lifecycle,
            policy=policy,
            evaluated_at=evaluated_at,
        )

        if authorization.is_authorized():
            return [
                DecisionAuthorizedEvent(
                    intent_id=state.intent_id,
                    result=authorization,
                )
            ]

        return [
            DecisionRejectedEvent(
                intent_id=state.intent_id,
                result=authorization,
            )
        ]

    # --- Event → State transitions --------------------------------------------

    @staticmethod
    def _apply_created(
        state: TradingIntentState | None,
        event: BaseEvent,
        envelope: EventEnvelope,
    ) -> TradingIntentState:
        if state is not None:
            raise InvariantViolation("TradingIntent already exists")

        if not isinstance(event, TradingIntentCreatedEvent):
            raise InvariantViolation("Invalid event type")

        return TradingIntentState(
            last_sequence=envelope.sequence,
            intent_id=event.intent_id,
            symbol=event.symbol,
            side=event.side,
            decision_identity=event.decision_identity,
            context=event.trading_context,
            authorization_result=None,
        )

    @staticmethod
    def _apply_authorized(
        state: TradingIntentState,
        event: BaseEvent,
        envelope: EventEnvelope,
    ) -> TradingIntentState:
        if state.authorization_result is not None:
            raise InvariantViolation("Authorization already decided")

        if not isinstance(event, DecisionAuthorizedEvent):
            raise InvariantViolation("Invalid event type")

        return TradingIntentState(
            last_sequence=envelope.sequence,
            intent_id=state.intent_id,
            symbol=state.symbol,
            side=state.side,
            decision_identity=state.decision_identity,
            context=state.context,
            authorization_result=event.result,
        )

    @staticmethod
    def _apply_rejected(
        state: TradingIntentState,
        event: BaseEvent,
        envelope: EventEnvelope,
    ) -> TradingIntentState:
        if state.authorization_result is not None:
            raise InvariantViolation("Authorization already decided")

        if not isinstance(event, DecisionRejectedEvent):
            raise InvariantViolation("Invalid event type")

        return TradingIntentState(
            last_sequence=envelope.sequence,
            intent_id=state.intent_id,
            symbol=state.symbol,
            side=state.side,
            decision_identity=state.decision_identity,
            context=state.context,
            authorization_result=event.result,
        )

    @classmethod
    def _handlers(
        cls,
    ) -> Mapping[type[BaseEvent], EventHandler[TradingIntentState, BaseEvent]]:
        return {
            TradingIntentCreatedEvent: cls._apply_created,
            DecisionAuthorizedEvent: cls._apply_authorized,
            DecisionRejectedEvent: cls._apply_rejected,
        }
