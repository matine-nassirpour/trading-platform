from dataclasses import dataclass

from quantum.domain.shared_kernel.errors.invariants import InvariantViolation
from quantum.domain.shared_kernel.primitives.value_object import ValueObject
from quantum.domain.trading.execution.order.execution_id import ExecutionId
from quantum.domain.trading.execution.taxonomy.liquidity_side import LiquiditySide


@dataclass(frozen=True, slots=True)
class ExecutionMetadata(ValueObject):
    """
    Execution context metadata.

    Non-economic, non-financial, descriptive only.
    """

    execution_id: ExecutionId
    liquidity: LiquiditySide

    def _validate(self) -> None:
        if not isinstance(self.execution_id, ExecutionId):
            raise InvariantViolation("ExecutionMetadata requires a valid ExecutionId")

        if not isinstance(self.liquidity, LiquiditySide):
            raise InvariantViolation("ExecutionMetadata requires a valid LiquiditySide")
