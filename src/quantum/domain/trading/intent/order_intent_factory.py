from __future__ import annotations

from dataclasses import dataclass
from typing import Final

from quantum.domain.shared.errors.invariants import InvariantViolation
from quantum.domain.shared.value_objects.epoch_ms import EpochMs
from quantum.domain.shared.value_objects.symbol import Symbol
from quantum.domain.trading.events.v1.order_intent_event import OrderIntentEvent
from quantum.domain.trading.risk.exit_policy import ExitPolicy
from quantum.domain.trading.types.order_type import OrderType
from quantum.domain.trading.types.position_side import PositionSide
from quantum.domain.trading.types.time_in_force import TimeInForce
from quantum.domain.trading.value_objects.identifiers import IntentId
from quantum.domain.trading.value_objects.instrument_spec import InstrumentSpec
from quantum.domain.trading.value_objects.price import Price
from quantum.domain.trading.value_objects.reference_price import ReferencePrice
from quantum.domain.trading.value_objects.volume import PositiveVolume


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

    volume: PositiveVolume

    reference_price: ReferencePrice | None = None
    limit_price: Price | None = None
    stop_price: Price | None = None

    sl: Price | None = None
    tp: Price | None = None

    time_in_force: TimeInForce = TimeInForce.GTC
    rationale: str | None = None

    decision_epoch_ms: EpochMs | None = None


class OrderIntentFactory:
    """
    Canonical domain factory for OrderIntentEvent.

    Responsibilities:
    - Enforce ALL order-type price invariants
    - Enforce SL / TP correctness via ExitPolicy
    - Produce a valid OrderIntentEvent or fail deterministically
    """

    # --- OrderType → price rules (explicit & auditable) -----------------------

    _REQUIRES_LIMIT: Final[set[OrderType]] = {
        OrderType.BUY_LIMIT,
        OrderType.SELL_LIMIT,
        OrderType.BUY_STOP_LIMIT,
        OrderType.SELL_STOP_LIMIT,
    }

    _REQUIRES_STOP: Final[set[OrderType]] = {
        OrderType.BUY_STOP,
        OrderType.SELL_STOP,
        OrderType.BUY_STOP_LIMIT,
        OrderType.SELL_STOP_LIMIT,
    }

    _FORBIDS_LIMIT: Final[set[OrderType]] = {
        OrderType.BUY,
        OrderType.SELL,
        OrderType.BUY_STOP,
        OrderType.SELL_STOP,
    }

    _FORBIDS_STOP: Final[set[OrderType]] = {
        OrderType.BUY,
        OrderType.SELL,
        OrderType.BUY_LIMIT,
        OrderType.SELL_LIMIT,
    }

    # --- Validation rules -----------------------------------------------------

    @staticmethod
    def _validate_price_requirements(params: OrderIntentParameters) -> None:
        t = params.order_type

        if t in OrderIntentFactory._REQUIRES_LIMIT and params.limit_price is None:
            raise InvariantViolation(f"{t} requires limit_price")

        if t in OrderIntentFactory._REQUIRES_STOP and params.stop_price is None:
            raise InvariantViolation(f"{t} requires stop_price")

        if t in OrderIntentFactory._FORBIDS_LIMIT and params.limit_price is not None:
            raise InvariantViolation(f"{t} forbids limit_price")

        if t in OrderIntentFactory._FORBIDS_STOP and params.stop_price is not None:
            raise InvariantViolation(f"{t} forbids stop_price")

        if t.requires_price() and not (params.limit_price or params.stop_price):
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
        occurred_at: EpochMs,
    ) -> OrderIntentEvent:
        """
        Validates and creates an OrderIntentEvent.

        This method is the SINGLE valid way to emit OrderIntentEvent.
        """

        OrderIntentFactory._validate_price_requirements(params)
        OrderIntentFactory._validate_sl_tp(params, instrument)

        return OrderIntentEvent(
            occurred_at=occurred_at.to_datetime(),
            intent_id=params.intent_id,
            symbol=params.symbol,
            type=params.order_type,
            volume=params.volume,
            reference_price=params.reference_price,
            stop_price=params.stop_price,
            limit_price=params.limit_price,
            sl=params.sl,
            tp=params.tp,
            time_in_force=params.time_in_force,
            rationale=params.rationale,
        )
