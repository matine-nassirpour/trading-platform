from dataclasses import dataclass

from quantum.domain.model.exceptions.validation_exceptions import InvariantViolation
from quantum.domain.model.value_objects.execution_id import ExecutionId
from quantum.domain.model.value_objects.fee import Fee
from quantum.domain.model.value_objects.price import Price
from quantum.domain.model.value_objects.time import EpochMs
from quantum.domain.model.value_objects.volume import PositiveVolume
from quantum.domain.types.execution import LiquiditySide


@dataclass(frozen=True)
class Fill:
    """
    Canonical execution fill (atomic).

    Immutable and audit-safe.
    """

    execution_id: ExecutionId
    price: Price
    volume: PositiveVolume
    liquidity: LiquiditySide
    fee: Fee
    executed_at: EpochMs

    def __post_init__(self) -> None:
        if not isinstance(self.executed_at, EpochMs):
            raise InvariantViolation("Fill must have a valid execution timestamp")

        if self.fee.value.is_nan() or self.fee.value.is_infinite():
            raise InvariantViolation("Fee must be finite")
