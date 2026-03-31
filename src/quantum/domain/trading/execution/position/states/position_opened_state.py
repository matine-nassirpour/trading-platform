from dataclasses import dataclass

from quantum.domain.shared_kernel.foundation.errors.invariants import InvariantViolation
from quantum.domain.shared_kernel.modeling.monetary.price import Price
from quantum.domain.trading.execution.position.states.position_state_base import (
    PositionStateBase,
)
from quantum.domain.trading.execution.position_side import PositionSide
from quantum.domain.trading.identifiers.position_id import PositionId
from quantum.domain.trading.value_objects.volume import PositiveVolume


@dataclass(frozen=True, slots=True)
class PositionOpenedState(PositionStateBase):

    position_id: PositionId
    side: PositionSide
    volume: PositiveVolume
    entry_price: Price
    closed: bool

    def _validate_semantics(self) -> None:
        super()._validate_semantics()

        if not isinstance(self.position_id, PositionId):
            raise InvariantViolation("PositionOpenedState.position_id invalid")

        if not isinstance(self.side, PositionSide):
            raise InvariantViolation("PositionOpenedState.side invalid")

        if not isinstance(self.volume, PositiveVolume):
            raise InvariantViolation("PositionOpenedState.volume invalid")

        if not isinstance(self.entry_price, Price):
            raise InvariantViolation("PositionOpenedState.entry_price invalid")

        if self.last_sequence.is_initial():
            raise InvariantViolation("Opened position cannot be initial")
