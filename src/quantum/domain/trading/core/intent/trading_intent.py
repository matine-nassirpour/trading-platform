from collections.abc import Mapping
from dataclasses import dataclass

from quantum.domain.shared_kernel.errors.invariants import (
    InvalidStateTransition,
    InvariantViolation,
)
from quantum.domain.shared_kernel.events.base_event import BaseEvent
from quantum.domain.shared_kernel.events.event_envelope import EventEnvelope
from quantum.domain.shared_kernel.events.event_sequence import EventSequence
from quantum.domain.shared_kernel.primitives.aggregate_state import AggregateState
from quantum.domain.shared_kernel.primitives.event_sourced_aggregate_root import (
    EventHandler,
    EventSourcedAggregateRoot,
)
from quantum.domain.shared_kernel.value_objects.price import Price
from quantum.domain.shared_kernel.value_objects.symbol import Symbol
from quantum.domain.shared_kernel.value_objects.volume import PositiveVolume
from quantum.domain.trading.core.decision.identity.decision_identity import (
    DecisionIdentity,
)
from quantum.domain.trading.events.v1.decision.order_intent_created_event import (
    OrderIntentCreatedEvent,
)
from quantum.domain.trading.events.v1.execution.order_created_event import (
    OrderCreatedEvent,
)
from quantum.domain.trading.events.v1.execution.order_submitted_event import (
    OrderSubmittedEvent,
)
from quantum.domain.trading.execution.order.order_type import OrderType
from quantum.domain.trading.execution.order.position_side import PositionSide
from quantum.domain.trading.execution.order.time_in_force import TimeInForce
from quantum.domain.trading.market.value_objects.reference_price import ReferencePrice
from quantum.domain.trading.value_objects.identifiers.intent_id import IntentId
from quantum.domain.trading.value_objects.identifiers.order_id import OrderId


@dataclass(frozen=True, slots=True)
class TradingIntentStateData(AggregateState):
    last_sequence: EventSequence

    intent_id: IntentId
    symbol: Symbol
    decision_identity: DecisionIdentity

    submitted: bool
    orders: frozenset[OrderId]

    def last_event_sequence(self) -> EventSequence:
        return self.last_sequence

    def _validate(self) -> None:
        if not isinstance(self.intent_id, IntentId):
            raise InvariantViolation("Invalid IntentId")

        if not isinstance(self.symbol, Symbol):
            raise InvariantViolation("Invalid Symbol")

        if not isinstance(self.decision_identity, DecisionIdentity):
            raise InvariantViolation("Invalid DecisionIdentity")

        if not isinstance(self.submitted, bool):
            raise InvariantViolation("Invalid submitted flag")

        if not isinstance(self.orders, frozenset):
            raise InvariantViolation("Orders must be a frozen set")

        for oid in self.orders:
            if not isinstance(oid, OrderId):
                raise InvariantViolation("Invalid OrderId in orders set")


class TradingIntent(EventSourcedAggregateRoot[TradingIntentStateData]):
    """
    Event-sourced TradingIntent aggregate.

    Represents:
    - a governed trading decision
    - the root of all derived orders
    - an auditable decision boundary
    """

    # --- Factory --------------------------------------------------------------

    @staticmethod
    def create(
        *,
        intent_id: IntentId,
        symbol: Symbol,
        decision_identity: DecisionIdentity,
    ) -> list[BaseEvent]:
        """
        Answers the question:
            "Can a trading intent be created for this decision,
             and what facts must be recorded to represent it?"

        This method represents a DOMAIN COMMAND.
        """

        return [
            OrderIntentCreatedEvent(
                intent_id=intent_id,
                symbol=symbol,
                decision_identity=decision_identity,
            )
        ]

    # --- Commands -------------------------------------------------------------

    def submit(self) -> list[BaseEvent]:
        """
        Answers the question:
            "Can this trading intent be submitted for execution?"

        This method represents a DOMAIN COMMAND.
        """

        state = self.state

        if state.submitted:
            raise InvalidStateTransition("TradingIntent already submitted")

        return [
            OrderSubmittedEvent(
                intent_id=state.intent_id,
                symbol=state.symbol,
            )
        ]

    def attach_order(
        self,
        *,
        order_id: OrderId,
        order_type: OrderType,
        side: PositionSide,
        volume: PositiveVolume,
        reference_price: ReferencePrice | None = None,
        stop_price: Price | None = None,
        limit_price: Price | None = None,
        sl: Price | None = None,
        tp: Price | None = None,
        time_in_force: TimeInForce | None = None,
    ) -> list[BaseEvent]:
        """
        Answers the question:
            "Can an order be attached to this trading intent,
             and if so, how must it be recorded?"

        This method represents a DOMAIN COMMAND.
        """

        state = self.state

        if not state.submitted:
            raise InvalidStateTransition("Cannot attach order before intent submission")

        if order_id in state.orders:
            raise InvariantViolation("Order already attached to TradingIntent")

        time_in_force = (
            time_in_force if time_in_force is not None else TimeInForce("gtc")
        )

        return [
            OrderCreatedEvent(
                intent_id=state.intent_id,
                order_id=order_id,
                symbol=state.symbol,
                order_type=order_type,
                side=side,
                volume=volume,
                reference_price=reference_price,
                stop_price=stop_price,
                limit_price=limit_price,
                sl=sl,
                tp=tp,
                time_in_force=time_in_force,
            )
        ]

    # --- Event → State transitions --------------------------------------------

    @staticmethod
    def _apply_created(
        state: TradingIntentStateData | None,
        event: BaseEvent,
        envelope: EventEnvelope,
    ) -> TradingIntentStateData:
        """
        Answers the question:
            "Given that a trading intent was created,
             what is the resulting aggregate state?"

        This method represents a PURE EVENT → STATE TRANSITION.
        """

        if state is not None:
            raise InvariantViolation("TradingIntent already exists")

        assert isinstance(event, OrderIntentCreatedEvent)

        return TradingIntentStateData(
            last_sequence=envelope.sequence,
            intent_id=event.intent_id,
            symbol=event.symbol,
            decision_identity=event.decision_identity,
            submitted=False,
            orders=frozenset(),
        )

    @staticmethod
    def _apply_submitted(
        state: TradingIntentStateData,
        event: BaseEvent,
        envelope: EventEnvelope,
    ) -> TradingIntentStateData:
        """
        Answers the question:
            "Given that the intent was submitted,
             how does the aggregate state change?"

        This method represents a PURE EVENT → STATE TRANSITION.
        """

        assert isinstance(event, OrderSubmittedEvent)
        return TradingIntentStateData(
            last_sequence=envelope.sequence,
            intent_id=state.intent_id,
            symbol=state.symbol,
            decision_identity=state.decision_identity,
            submitted=True,
            orders=state.orders,
        )

    @staticmethod
    def _apply_attached(
        state: TradingIntentStateData,
        event: BaseEvent,
        envelope: EventEnvelope,
    ) -> TradingIntentStateData:
        """
        Answers the question:
            "Given that an order was attached to this intent,
             how does the aggregate state evolve?"

        This method represents a PURE EVENT → STATE TRANSITION.
        """

        assert isinstance(event, OrderCreatedEvent)
        return TradingIntentStateData(
            last_sequence=envelope.sequence,
            intent_id=state.intent_id,
            symbol=state.symbol,
            decision_identity=state.decision_identity,
            submitted=state.submitted,
            orders=state.orders | {event.order_id},
        )

    @classmethod
    def _handlers(
        cls,
    ) -> Mapping[type[BaseEvent], EventHandler[TradingIntentStateData, BaseEvent]]:
        return {
            OrderIntentCreatedEvent: cls._apply_created,
            OrderSubmittedEvent: cls._apply_submitted,
            OrderCreatedEvent: cls._apply_attached,
        }
