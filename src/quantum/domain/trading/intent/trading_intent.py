from collections.abc import Mapping
from types import MappingProxyType

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
from quantum.domain.decision.identity.strategy_id import StrategyId
from quantum.domain.risk.capital.capital_allocation_intent import (
    CapitalAllocationIntent,
)
from quantum.domain.risk.events.v1.capital_allocated_event import CapitalAllocatedEvent
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
from quantum.domain.trading.intent.trading_intent_initialized_state import (
    TradingIntentInitializedState,
)
from quantum.domain.trading.intent.trading_intent_state_base import (
    TradingIntentStateBase,
)
from quantum.domain.trading.intent.trading_intent_uninitialized_state import (
    TradingIntentUninitializedState,
)


class TradingIntent(EventSourcedAggregateRoot[TradingIntentStateBase]):
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

    __slots__ = ()

    @classmethod
    def empty_state(cls) -> TradingIntentStateBase:
        return TradingIntentUninitializedState(last_sequence=EventSequence.initial())

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

    def evaluate(
        self,
        *,
        policy: DecisionPolicy,
        lifecycle: StrategyLifecycle,
        evaluated_at: EpochMs,
    ) -> list[BaseEvent]:

        state = self.state

        if isinstance(state, TradingIntentUninitializedState):
            raise InvalidStateTransition("Cannot evaluate uninitialized TradingIntent")

        assert isinstance(state, TradingIntentInitializedState)

        if state.is_evaluated():
            raise InvalidStateTransition("TradingIntent already evaluated")

        lifecycle_result = StrategyEligibilityPolicy.evaluate(
            lifecycle=lifecycle,
            at=evaluated_at,
        )

        if lifecycle_result.is_rejected():
            return [
                DecisionRejectedEvent(
                    intent_id=state.intent_id,
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
                    intent_id=state.intent_id,
                    reason_code=policy_result.reason_code,
                )
            ]

        return [
            DecisionAuthorizedEvent(
                intent_id=state.intent_id,
            )
        ]

    def allocate_capital(
        self,
        *,
        allocation: CapitalAllocationIntent,
    ) -> list[BaseEvent]:
        """
        Commits the capital allocation intent for this TradingIntent.

        HARD GUARANTEES:
        - Only allowed AFTER authorization
        - Idempotent: cannot allocate twice
        - Fully auditable and replayable
        """

        state = self.state

        if isinstance(state, TradingIntentUninitializedState):
            raise InvalidStateTransition(
                "Cannot allocate capital on uninitialized intent"
            )

        assert isinstance(state, TradingIntentInitializedState)

        if not state.is_evaluated():
            raise InvalidStateTransition("Cannot allocate capital before evaluation")

        if not state.is_authorized():
            raise InvalidStateTransition(
                "Cannot allocate capital for a rejected intent"
            )

        if state.is_capital_allocated():
            raise InvalidStateTransition("Capital already allocated")

        # Extract strategy_id from decision identity (strict)
        strategy_id = getattr(state.decision_identity, "strategy_id", None)
        if not isinstance(strategy_id, StrategyId):
            raise InvariantViolation(
                "DecisionIdentity must expose a valid strategy_id to emit CapitalAllocatedEvent"
            )

        return [
            CapitalAllocatedEvent(
                strategy_id=strategy_id,
                allocation=allocation,
            )
        ]

    # --- Event → State transitions --------------------------------------------

    @staticmethod
    def _apply_created(
        state: TradingIntentStateBase,
        event: BaseEvent,
        envelope: EventEnvelope,
    ) -> TradingIntentStateBase:

        if not isinstance(state, TradingIntentUninitializedState):
            raise InvariantViolation("TradingIntent already exists")

        if not isinstance(event, TradingIntentCreatedEvent):
            raise InvariantViolation("Invalid event type")

        return TradingIntentInitializedState(
            last_sequence=envelope.sequence,
            intent_id=event.intent_id,
            symbol=event.symbol,
            side=event.side,
            decision_identity=event.decision_identity,
            context=event.trading_context,
            authorization_result=None,
            capital_allocation=None,
        )

    @staticmethod
    def _apply_authorized(
        state: TradingIntentStateBase,
        event: BaseEvent,
        envelope: EventEnvelope,
    ) -> TradingIntentStateBase:

        if not isinstance(state, TradingIntentInitializedState):
            raise InvariantViolation("TradingIntent not initialized")

        if not isinstance(event, DecisionAuthorizedEvent):
            raise InvariantViolation("Invalid event type")

        if state.is_evaluated():
            raise InvariantViolation("Already evaluated")

        return TradingIntentInitializedState(
            last_sequence=envelope.sequence,
            intent_id=state.intent_id,
            symbol=state.symbol,
            side=state.side,
            decision_identity=state.decision_identity,
            context=state.context,
            authorization_result=DecisionAuthorizationResult.authorized(),
            capital_allocation=state.capital_allocation,  # should be None here
        )

    @staticmethod
    def _apply_rejected(
        state: TradingIntentStateBase,
        event: BaseEvent,
        envelope: EventEnvelope,
    ) -> TradingIntentStateBase:

        if not isinstance(state, TradingIntentInitializedState):
            raise InvariantViolation("TradingIntent not initialized")

        if not isinstance(event, DecisionRejectedEvent):
            raise InvariantViolation("Invalid event type")

        if state.is_evaluated():
            raise InvariantViolation("Already evaluated")

        return TradingIntentInitializedState(
            last_sequence=envelope.sequence,
            intent_id=state.intent_id,
            symbol=state.symbol,
            side=state.side,
            decision_identity=state.decision_identity,
            context=state.context,
            authorization_result=DecisionAuthorizationResult.rejected(
                reason_code=event.reason_code
            ),
            capital_allocation=None,  # explicit: cannot have allocation if rejected
        )

    @staticmethod
    def _apply_capital_allocated(
        state: TradingIntentStateBase,
        event: BaseEvent,
        envelope: EventEnvelope,
    ) -> TradingIntentStateBase:
        if not isinstance(state, TradingIntentInitializedState):
            raise InvariantViolation("TradingIntent not initialized")

        if not isinstance(event, CapitalAllocatedEvent):
            raise InvariantViolation("Invalid event type")

        if not state.is_authorized():
            raise InvariantViolation(
                "Cannot allocate capital unless intent is authorized"
            )

        if state.is_capital_allocated():
            raise InvariantViolation("Capital already allocated")

        return TradingIntentInitializedState(
            last_sequence=envelope.sequence,
            intent_id=state.intent_id,
            symbol=state.symbol,
            side=state.side,
            decision_identity=state.decision_identity,
            context=state.context,
            authorization_result=state.authorization_result,
            capital_allocation=event.allocation,
        )

    @classmethod
    def _handlers(
        cls,
    ) -> Mapping[type[BaseEvent], EventHandler]:
        return MappingProxyType(
            {
                TradingIntentCreatedEvent: cls._apply_created,
                DecisionAuthorizedEvent: cls._apply_authorized,
                DecisionRejectedEvent: cls._apply_rejected,
                CapitalAllocatedEvent: cls._apply_capital_allocated,
            }
        )
