from __future__ import annotations

from dataclasses import dataclass

from quantum.domain.shared_kernel.errors.invariants import InvariantViolation
from quantum.domain.shared_kernel.value_objects.epoch_ms import EpochMs
from quantum.domain.shared_kernel.value_objects.price import Price
from quantum.domain.shared_kernel.value_objects.symbol import Symbol
from quantum.domain.shared_kernel.value_objects.volume import PositiveVolume
from quantum.domain.trading.context.trading_context import TradingContext
from quantum.domain.trading.decision.boundary.decision_boundary import DecisionBoundary
from quantum.domain.trading.decision.boundary.decision_boundary_policy import (
    DecisionBoundaryPolicy,
)
from quantum.domain.trading.decision.decision_identity import DecisionIdentity
from quantum.domain.trading.events.v1.decision_authorized_event import (
    DecisionAuthorizedEvent,
)
from quantum.domain.trading.events.v1.order_intent_event import OrderIntentEvent
from quantum.domain.trading.risk.exit_policy import ExitPolicy
from quantum.domain.trading.value_objects.identifiers.intent_id import IntentId
from quantum.domain.trading.value_objects.instrument.instrument_spec import (
    InstrumentSpec,
)
from quantum.domain.trading.value_objects.market.reference_price import ReferencePrice
from quantum.domain.trading.value_objects.order.order_type import OrderType
from quantum.domain.trading.value_objects.order.position_side import PositionSide
from quantum.domain.trading.value_objects.order.time_in_force import TimeInForce


@dataclass(frozen=True)
class OrderIntentParameters:
    """
    Canonical parameter object for an order intent decision.

    This object is NOT persisted.
    It exists only to validate invariants before event emission.
    """

    intent_id: IntentId
    symbol: Symbol
    order_type: OrderType
    side: PositionSide

    trading_context: TradingContext
    decision_identity: DecisionIdentity

    volume: PositiveVolume

    reference_price: ReferencePrice | None = None
    stop_price: Price | None = None
    limit_price: Price | None = None

    sl: Price | None = None
    tp: Price | None = None

    time_in_force: TimeInForce = TimeInForce("gtc")


class OrderIntentFactory:
    """
    Canonical domain factory for OrderIntentEvent.
    """

    # --- Validation rules -----------------------------------------------------

    @staticmethod
    def _validate_price_requirements(params: OrderIntentParameters) -> None:
        t = params.order_type

        if t.requires_limit_price() and params.limit_price is None:
            raise InvariantViolation(f"{t} requires limit_price")

        if t.requires_stop_price() and params.stop_price is None:
            raise InvariantViolation(f"{t} requires stop_price")

        if t.forbids_limit_price() and params.limit_price is not None:
            raise InvariantViolation(f"{t} forbids limit_price")

        if t.forbids_stop_price() and params.stop_price is not None:
            raise InvariantViolation(f"{t} forbids stop_price")

        if t.requires_price_reference() and not (
            params.limit_price or params.stop_price or params.reference_price
        ):
            raise InvariantViolation(f"{t} requires a price reference")

    @staticmethod
    def _validate_sl_tp(
        params: OrderIntentParameters,
        instrument: InstrumentSpec,
    ) -> None:
        if params.sl or params.tp:
            entry = params.reference_price or params.limit_price or params.stop_price
            if entry is None:
                raise InvariantViolation(
                    "SL/TP defined but no reference entry price available"
                )

            ExitPolicy.validate(
                side=params.side,
                entry=entry,
                sl=params.sl,
                tp=params.tp,
                instrument=instrument,
            )

    # --- Public API -----------------------------------------------------------

    @staticmethod
    def create(
        *,
        params: OrderIntentParameters,
        instrument: InstrumentSpec,
        decision_boundary: DecisionBoundary,
        occurred_at: EpochMs,
    ) -> tuple[OrderIntentEvent, DecisionAuthorizedEvent]:
        """
        Validates and creates an OrderIntentEvent.

        Governance rules:
        - Decision MUST be authorized by a DecisionBoundary
        - Authorization result is explicitly emitted as an event

        Returns:
        - OrderIntentEvent
        - DecisionAuthorizedEvent
        """

        # --- Structural validation --------------------------------------------
        OrderIntentFactory._validate_price_requirements(params)
        OrderIntentFactory._validate_sl_tp(params, instrument)

        # --- Decision boundary evaluation -------------------------------------
        boundary_result = DecisionBoundaryPolicy.evaluate(
            boundary=decision_boundary,
            decision=params.decision_identity,
            context=params.trading_context,
        )

        if not boundary_result.authorized:
            raise InvariantViolation(boundary_result.reason)

        decision_authorized_event = DecisionAuthorizedEvent(
            occurred_at=occurred_at,
            intent_id=params.intent_id,
            result=boundary_result,
        )

        # --- Intent emission --------------------------------------------------
        order_intent_event = OrderIntentEvent(
            occurred_at=occurred_at,
            intent_id=params.intent_id,
            symbol=params.symbol,
            order_type=params.order_type,
            side=params.side,
            trading_context=params.trading_context,
            decision_identity=params.decision_identity,
            volume=params.volume,
            reference_price=params.reference_price,
            stop_price=params.stop_price,
            limit_price=params.limit_price,
            sl=params.sl,
            tp=params.tp,
            time_in_force=params.time_in_force,
        )

        return order_intent_event, decision_authorized_event
