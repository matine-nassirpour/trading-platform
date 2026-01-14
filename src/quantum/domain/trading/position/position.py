from __future__ import annotations

from quantum.domain.shared_kernel.errors.invariants import InvariantViolation
from quantum.domain.shared_kernel.errors.position_errors import PositionAlreadyClosed
from quantum.domain.shared_kernel.money.money_context import MoneyContext
from quantum.domain.shared_kernel.primitives.event_sourced_aggregate_root import (
    EventSourcedAggregateRoot,
)
from quantum.domain.shared_kernel.value_objects.price import Price
from quantum.domain.shared_kernel.value_objects.volume import PositiveVolume
from quantum.domain.trading.events.v1.position_closed_event import PositionClosedEvent
from quantum.domain.trading.events.v1.position_opened_event import PositionOpenedEvent
from quantum.domain.trading.execution.order.position_side import PositionSide
from quantum.domain.trading.position.pnl_service import PnLService
from quantum.domain.trading.value_objects.identifiers.position_id import PositionId


class Position(EventSourcedAggregateRoot):
    position_id: PositionId
    side: PositionSide
    volume: PositiveVolume
    entry_price: Price
    closed: bool = False

    # --- Factory --------------------------------------------------------------

    @staticmethod
    def open(
        *,
        position_id: PositionId,
        side: PositionSide,
        volume: PositiveVolume,
        entry_price: Price,
    ) -> Position:
        pos = Position.__new__(Position)
        EventSourcedAggregateRoot.__init__(pos)

        pos._raise(
            PositionOpenedEvent(
                position_id=position_id,
                side=side,
                volume=volume,
                entry_price=entry_price,
            )
        )
        return pos

    # --- Commands -------------------------------------------------------------

    def close(
        self,
        *,
        exit_price: Price,
        context: MoneyContext,
    ) -> None:
        if self.closed:
            raise PositionAlreadyClosed("Position already closed")

        pnl = PnLService.compute_realized_pnl(
            entry_price=self.entry_price,
            exit_price=exit_price,
            volume=self.volume,
            side=self.side,
            context=context,
        )

        self._raise(
            PositionClosedEvent(
                position_id=self.position_id,
                side=self.side,
                volume=self.volume,
                exit_price=exit_price,
                realized_pnl=pnl,
            )
        )

    # --- Event application ----------------------------------------------------

    def _apply_position_opened_event(self, event: PositionOpenedEvent) -> None:
        self.position_id = event.position_id
        self.side = event.side
        self.volume = event.volume
        self.entry_price = event.entry_price
        self.closed = False

    def _apply_position_closed_event(self, event: PositionClosedEvent) -> None:
        self.closed = True

    # --- Aggregate invariants -------------------------------------------------

    def _validate_state(self) -> None:
        if not isinstance(self.position_id, PositionId):
            raise InvariantViolation("PositionId missing")

        if not isinstance(self.side, PositionSide):
            raise InvariantViolation("PositionSide missing")

        if not isinstance(self.volume, PositiveVolume):
            raise InvariantViolation("Volume missing")

        if not isinstance(self.entry_price, Price):
            raise InvariantViolation("Entry price missing")

        if not isinstance(self.closed, bool):
            raise InvariantViolation("Closed flag corrupted")
