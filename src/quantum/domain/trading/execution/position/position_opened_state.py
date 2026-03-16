from dataclasses import dataclass

from quantum.domain.shared_kernel.errors.invariants import InvariantViolation
from quantum.domain.shared_kernel.identifiers.position_id import PositionId
from quantum.domain.shared_kernel.value_objects.position_side import PositionSide
from quantum.domain.shared_kernel.value_objects.price import Price
from quantum.domain.shared_kernel.value_objects.volume import PositiveVolume
from quantum.domain.trading.execution.position.position_state_base import (
    PositionStateBase,
)


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
