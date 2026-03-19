from dataclasses import dataclass

from quantum.domain.market.value_objects.position_side import PositionSide
from quantum.domain.shared_kernel.foundation.errors.invariants import InvariantViolation
from quantum.domain.shared_kernel.monetary.price import Price
from quantum.domain.trading.execution.position.position_state_base import (
    PositionStateBase,
)
from quantum.domain.trading.identifiers.position_id import PositionId
from quantum.domain.trading.value_objects.volume import PositiveVolume


@dataclass(frozen=True, slots=True)
class PositionOpenedState(PositionStateBase):

    position_id: PositionId
    side: PositionSide
    volume: PositiveVolume
    entry_price: Price
    closed: bool

    def _validate(self):
        if self.last_sequence.is_initial():
            raise InvariantViolation("Opened position cannot be initial")
