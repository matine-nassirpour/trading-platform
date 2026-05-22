from dataclasses import dataclass

from quantum.domain.shared_kernel.foundation.errors.invariants import InvariantViolation
from quantum.domain.shared_kernel.modeling.monetary.pnl import RealizedPnL
from quantum.domain.shared_kernel.modeling.monetary.price import Price
from quantum.domain.trading.common.value_objects.position_side import PositionSide
from quantum.domain.trading.common.value_objects.volume import PositiveVolume
from quantum.domain.trading.identity.broker_position_ref import BrokerPositionRef
from quantum.domain.trading.position.states.position_state_base import PositionStateBase


@dataclass(frozen=True, slots=True)
class PositionClosedState(PositionStateBase):
    broker_position_ref: BrokerPositionRef
    side: PositionSide
    volume: PositiveVolume
    entry_price: Price
    exit_price: Price
    realized_pnl: RealizedPnL

    def _validate_semantics(self) -> None:
        super()._validate_semantics()

        if not isinstance(self.broker_position_ref, BrokerPositionRef):
            raise InvariantViolation("PositionClosedState.broker_position_ref invalid")

        if not isinstance(self.side, PositionSide):
            raise InvariantViolation("PositionClosedState.side invalid")

        if not isinstance(self.volume, PositiveVolume):
            raise InvariantViolation("PositionClosedState.volume invalid")

        if not isinstance(self.entry_price, Price):
            raise InvariantViolation("PositionClosedState.entry_price invalid")

        if not isinstance(self.exit_price, Price):
            raise InvariantViolation("PositionClosedState.exit_price invalid")

        if not isinstance(self.realized_pnl, RealizedPnL):
            raise InvariantViolation("PositionClosedState.realized_pnl invalid")

        if self.last_sequence.is_initial():
            raise InvariantViolation("Closed position cannot be initial")
