from collections.abc import Mapping
from typing import Self

from quantum.domain.decision.context.trading_context import TradingContext
from quantum.domain.decision.events.v1.decision_authorized_event import (
    DecisionAuthorizedEvent,
)
from quantum.domain.decision.events.v1.decision_rejected_event import (
    DecisionRejectedEvent,
)
from quantum.domain.decision.events.v1.trading_intent_created_event import (
    TradingIntentCreatedEvent,
)
from quantum.domain.decision.governance.decision_authorization_result import (
    DecisionAuthorizationResult,
)
from quantum.domain.decision.governance.decision_policy import DecisionPolicy
from quantum.domain.decision.governance.decision_policy_evaluator import (
    DecisionPolicyEvaluator,
)
from quantum.domain.decision.identity.decision_identity import DecisionIdentity
from quantum.domain.decision.lifecycle.strategy_eligibility_policy import (
    StrategyEligibilityPolicy,
)
from quantum.domain.decision.lifecycle.strategy_lifecycle import StrategyLifecycle
from quantum.domain.decision.trading_intent.trading_intent_initialized_state import (
    TradingIntentInitializedState,
)
from quantum.domain.decision.trading_intent.trading_intent_state_base import (
    TradingIntentStateBase,
)
from quantum.domain.decision.trading_intent.trading_intent_uninitialized_state import (
    TradingIntentUninitializedState,
)
from quantum.domain.shared_kernel.errors.invariants import (
    InvalidStateTransition,
    InvariantViolation,
)
from quantum.domain.shared_kernel.events.base.base_event import BaseEvent
from quantum.domain.shared_kernel.events.event_sequence import EventSequence
from quantum.domain.shared_kernel.events.recorded_event_envelope import (
    RecordedEventEnvelope,
)
from quantum.domain.shared_kernel.identifiers.intent_id import IntentId
from quantum.domain.shared_kernel.primitives.event_sourced_aggregate_root import (
    EventHandler,
    EventSourcedAggregateRoot,
)
from quantum.domain.shared_kernel.value_objects.epoch_ms import EpochMs
from quantum.domain.shared_kernel.value_objects.position_side import PositionSide
from quantum.domain.shared_kernel.value_objects.symbol import Symbol


class TradingIntent(EventSourcedAggregateRoot[IntentId, TradingIntentStateBase]):
    """
    TradingIntent — Decision Aggregate (PURE DOMAIN)

    Responsibilities:
    - represent a trading decision
    - carry decision identity and context
    - track authorization outcome
    - emit governance events

    Explicitly DOES NOT:
    - reserve or allocate capital
    - create orders
    - know about execution
    - perform pricing
    """

    __slots__ = ()

    @classmethod
    def aggregate_id_type(cls) -> type[IntentId]:
        return IntentId

    @classmethod
    def state_type(cls) -> type[TradingIntentStateBase]:
        return TradingIntentStateBase

    @classmethod
    def uninitialized_state(cls) -> TradingIntentStateBase:
        return TradingIntentUninitializedState(
            last_sequence=EventSequence.initial(),
        )

    # --- Internal helpers -----------------------------------------------------

    @staticmethod
    def _assert_event_matches_stream_identity(
        *,
        event_intent_id: IntentId,
        envelope: RecordedEventEnvelope,
    ) -> None:
        if event_intent_id != envelope.aggregate_id:
            raise InvariantViolation(
                "Event intent_id does not match envelope aggregate_id"
            )

    def _require_initialized(self) -> TradingIntentInitializedState:
        state = self.state

        if isinstance(state, TradingIntentUninitializedState):
            raise InvalidStateTransition("TradingIntent not initialized")

        if not isinstance(state, TradingIntentInitializedState):
            raise InvariantViolation("Corrupted aggregate state")

        return state

    # --- Creation API ---------------------------------------------------------

    @classmethod
    def decide_create(
        cls,
        *,
        intent_id: IntentId,
        symbol: Symbol,
        side: PositionSide,
        decision_identity: DecisionIdentity,
        context: TradingContext,
    ) -> list[BaseEvent]:
        """
        Pure domain decision for creating a new TradingIntent.
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

    @classmethod
    def create_new(
        cls,
        *,
        aggregate_id: IntentId,
        symbol: Symbol,
        side: PositionSide,
        decision_identity: DecisionIdentity,
        context: TradingContext,
    ) -> tuple[Self, list[BaseEvent]]:
        """
        Canonical factory for a brand-new TradingIntent aggregate.

        Returns:
            - the canonical empty aggregate instance
            - the domain event(s) that must be persisted to create it

        The returned aggregate intentionally remains EMPTY until the recorded
        creation envelope is persisted and applied.
        """

        aggregate = cls.new(aggregate_id=aggregate_id)

        domain_events = cls.decide_create(
            intent_id=aggregate.aggregate_id,
            symbol=symbol,
            side=side,
            decision_identity=decision_identity,
            context=context,
        )

        return aggregate, domain_events

    # --- Commands -------------------------------------------------------------

    def evaluate(
        self,
        *,
        policy: DecisionPolicy,
        lifecycle: StrategyLifecycle,
        evaluated_at: EpochMs,
    ) -> list[BaseEvent]:
        """
        Evaluates the TradingIntent against lifecycle and governance policy.

        Outcome is terminal for authorization:
        - authorized
        - rejected
        """

        state = self._require_initialized()

        if state.is_evaluated():
            raise InvalidStateTransition("TradingIntent has already been evaluated")

        lifecycle_result = StrategyEligibilityPolicy.evaluate(
            lifecycle=lifecycle,
            at=evaluated_at,
        )

        if lifecycle_result.is_rejected():
            return [
                DecisionRejectedEvent(
                    intent_id=self.aggregate_id,
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
                DecisionRejectedEvent(
                    intent_id=self.aggregate_id,
                    reason_code=policy_result.reason_code,
                )
            ]

        return [
            DecisionAuthorizedEvent(
                intent_id=self.aggregate_id,
            )
        ]

    # --- Event → State transitions --------------------------------------------

    @staticmethod
    def _apply_created(
        state: TradingIntentStateBase,
        event: BaseEvent,
        envelope: RecordedEventEnvelope,
    ) -> TradingIntentStateBase:

        if not isinstance(state, TradingIntentUninitializedState):
            raise InvariantViolation("TradingIntent already exists")

        if not isinstance(event, TradingIntentCreatedEvent):
            raise InvariantViolation(
                "TradingIntent._apply_created requires TradingIntentCreatedEvent"
            )

        TradingIntent._assert_event_matches_stream_identity(
            event_intent_id=event.intent_id,
            envelope=envelope,
        )

        return TradingIntentInitializedState(
            last_sequence=envelope.sequence,
            symbol=event.symbol,
            side=event.side,
            decision_identity=event.decision_identity,
            context=event.trading_context,
            authorization_result=None,
        )

    @staticmethod
    def _apply_authorized(
        state: TradingIntentStateBase,
        event: BaseEvent,
        envelope: RecordedEventEnvelope,
    ) -> TradingIntentStateBase:

        if not isinstance(state, TradingIntentInitializedState):
            raise InvariantViolation("TradingIntent is not initialized")

        if not isinstance(event, DecisionAuthorizedEvent):
            raise InvariantViolation(
                "TradingIntent._apply_authorized requires DecisionAuthorizedEvent"
            )

        TradingIntent._assert_event_matches_stream_identity(
            event_intent_id=event.intent_id,
            envelope=envelope,
        )

        if state.is_evaluated():
            raise InvariantViolation("TradingIntent has already been evaluated")

        return TradingIntentInitializedState(
            last_sequence=envelope.sequence,
            symbol=state.symbol,
            side=state.side,
            decision_identity=state.decision_identity,
            context=state.context,
            authorization_result=DecisionAuthorizationResult.authorized(),
        )

    @staticmethod
    def _apply_rejected(
        state: TradingIntentStateBase,
        event: BaseEvent,
        envelope: RecordedEventEnvelope,
    ) -> TradingIntentStateBase:

        if not isinstance(state, TradingIntentInitializedState):
            raise InvariantViolation("TradingIntent is not initialized")

        if not isinstance(event, DecisionRejectedEvent):
            raise InvariantViolation(
                "TradingIntent._apply_rejected requires DecisionRejectedEvent"
            )

        TradingIntent._assert_event_matches_stream_identity(
            event_intent_id=event.intent_id,
            envelope=envelope,
        )

        if state.is_evaluated():
            raise InvariantViolation("TradingIntent has already been evaluated")

        return TradingIntentInitializedState(
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
    ) -> Mapping[type[BaseEvent], EventHandler[TradingIntentStateBase, BaseEvent]]:
        return {
            TradingIntentCreatedEvent: cls._apply_created,
            DecisionAuthorizedEvent: cls._apply_authorized,
            DecisionRejectedEvent: cls._apply_rejected,
        }
