from collections.abc import Mapping
from dataclasses import dataclass

from quantum.domain.decision.context.trading_context import TradingContext
from quantum.domain.decision.events.v1.decision_authorized_event import (
    DecisionAuthorizedEvent,
)
from quantum.domain.decision.events.v1.decision_rejected_event import (
    DecisionRejectedEvent,
)
from quantum.domain.decision.governance.decision_policy_result import (
    DecisionPolicyResult,
)
from quantum.domain.decision.identity.decision_identity import DecisionIdentity
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
from quantum.domain.trading.events.v1.execution.trading_intent_created_event import (
    TradingIntentCreatedEvent,
)


@dataclass(frozen=True, slots=True)
class TradingIntentState(AggregateState):
    """
    Immutable state of a TradingIntent.

    This state represents a GOVERNED DECISION,
    not an execution instruction.
    """

    last_sequence: EventSequence

    intent_id: IntentId
    decision_identity: DecisionIdentity
    context: TradingContext

    authorized: bool
    rejected: bool

    def last_event_sequence(self) -> EventSequence:
        return self.last_sequence

    def _validate(self) -> None:
        if not isinstance(self.intent_id, IntentId):
            raise InvariantViolation("TradingIntent requires a valid IntentId")

        if not isinstance(self.decision_identity, DecisionIdentity):
            raise InvariantViolation("TradingIntent requires DecisionIdentity")

        if not isinstance(self.context, TradingContext):
            raise InvariantViolation("TradingIntent requires TradingContext")

        if not isinstance(self.authorized, bool):
            raise InvariantViolation("authorized flag must be boolean")

        if not isinstance(self.rejected, bool):
            raise InvariantViolation("rejected flag must be boolean")

        if self.authorized and self.rejected:
            raise InvariantViolation(
                "TradingIntent cannot be both authorized and rejected"
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
                decision_identity=decision_identity,
                trading_context=context,
            )
        ]

    # --- Commands -------------------------------------------------------------

    def authorize(self, *, result: DecisionPolicyResult) -> list[BaseEvent]:
        """
        Confirms that the trading intent is authorized.

        This does NOT trigger execution.
        It only certifies that the decision is valid.
        """

        state = self.state

        if state.authorized:
            raise InvalidStateTransition("TradingIntent already authorized")

        if state.rejected:
            raise InvalidStateTransition("Rejected TradingIntent cannot be authorized")

        return [
            DecisionAuthorizedEvent(
                intent_id=self.state.intent_id,
                result=result,
            )
        ]

    def reject(self, *, result: DecisionPolicyResult) -> list[BaseEvent]:
        """
        Explicit rejection of the trading decision.
        """

        state = self.state

        if state.authorized:
            raise InvalidStateTransition("Authorized TradingIntent cannot be rejected")

        if state.rejected:
            raise InvalidStateTransition("TradingIntent already rejected")

        return [
            DecisionRejectedEvent(
                intent_id=self.state.intent_id,
                result=result,
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

        assert isinstance(event, TradingIntentCreatedEvent)

        return TradingIntentState(
            last_sequence=envelope.sequence,
            intent_id=event.intent_id,
            decision_identity=event.decision_identity,
            context=event.trading_context,
            authorized=False,
            rejected=False,
        )

    @staticmethod
    def _apply_authorized(
        state: TradingIntentState,
        event: BaseEvent,
        envelope: EventEnvelope,
    ) -> TradingIntentState:
        assert isinstance(event, DecisionAuthorizedEvent)

        return TradingIntentState(
            last_sequence=envelope.sequence,
            intent_id=state.intent_id,
            decision_identity=state.decision_identity,
            context=state.context,
            authorized=True,
            rejected=False,
        )

    @staticmethod
    def _apply_rejected(
        state: TradingIntentState,
        event: BaseEvent,
        envelope: EventEnvelope,
    ) -> TradingIntentState:
        assert isinstance(event, DecisionRejectedEvent)

        return TradingIntentState(
            last_sequence=envelope.sequence,
            intent_id=state.intent_id,
            decision_identity=state.decision_identity,
            context=state.context,
            authorized=False,
            rejected=True,
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
