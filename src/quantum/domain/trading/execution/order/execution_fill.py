from dataclasses import dataclass

from quantum.domain.shared_kernel.foundation.errors.invariants import InvariantViolation
from quantum.domain.shared_kernel.modeling.monetary.price import Price
from quantum.domain.shared_kernel.modeling.temporal.epoch_ms import EpochMs
from quantum.domain.shared_kernel.modeling.value_objects.value_object import ValueObject
from quantum.domain.trading.execution.order.execution_id import ExecutionId
from quantum.domain.trading.value_objects.volume import PositiveVolume


@dataclass(frozen=True, slots=True)
class ExecutionFill(ValueObject):
    """
    Atomic economic execution fill.

    Represents WHAT was executed, not HOW.
    """

    execution_id: ExecutionId
    price: Price
    volume: PositiveVolume
    executed_at: EpochMs

    def _validate_semantics(self) -> None:
        if not isinstance(self.execution_id, ExecutionId):
            raise InvariantViolation("ExecutionFill requires a valid ExecutionId")

        if not isinstance(self.price, Price):
            raise InvariantViolation("ExecutionFill requires a valid Price")

        if not isinstance(self.volume, PositiveVolume):
            raise InvariantViolation("ExecutionFill requires a valid PositiveVolume")

        if not isinstance(self.executed_at, EpochMs):
            raise InvariantViolation(
                "ExecutionFill requires a valid execution timestamp"
            )
