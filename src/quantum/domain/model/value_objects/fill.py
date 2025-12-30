from dataclasses import dataclass

from quantum.domain.model.exceptions.validation_exceptions import InvariantViolation
from quantum.domain.model.value_objects.base import ValueObject
from quantum.domain.model.value_objects.execution_id import ExecutionId
from quantum.domain.model.value_objects.fee import Fee
from quantum.domain.model.value_objects.price import Price
from quantum.domain.model.value_objects.time import EpochMs
from quantum.domain.model.value_objects.volume import PositiveVolume
from quantum.domain.types.execution import LiquiditySide


@dataclass(frozen=True)
class Fill(ValueObject):
    """
    Canonical execution fill (atomic).
    """

    execution_id: ExecutionId
    price: Price
    volume: PositiveVolume
    liquidity: LiquiditySide
    fee: Fee
    executed_at: EpochMs

    def _validate(self) -> None:
        if not isinstance(self.execution_id, ExecutionId):
            raise InvariantViolation("Fill must have a valid ExecutionId")

        if not isinstance(self.price, Price):
            raise InvariantViolation("Fill must have a valid Price")

        if not isinstance(self.volume, PositiveVolume):
            raise InvariantViolation("Fill must have a valid PositiveVolume")

        if not isinstance(self.liquidity, LiquiditySide):
            raise InvariantViolation("Fill must have a valid LiquiditySide")

        if not isinstance(self.fee, Fee):
            raise InvariantViolation("Fill must have a valid Fee")

        if not isinstance(self.executed_at, EpochMs):
            raise InvariantViolation("Fill must have a valid execution timestamp")

        # Fee invariants already enforced by Fee VO,
        # but we keep the semantic assertion explicit.
        if self.fee.value.is_nan() or self.fee.value.is_infinite():
            raise InvariantViolation("Fill fee must be finite")
