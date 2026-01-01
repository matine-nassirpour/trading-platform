from dataclasses import dataclass

from quantum.domain.execution.types.liquidity_side import LiquiditySide
from quantum.domain.execution.value_objects.execution_id import ExecutionId
from quantum.domain.execution.value_objects.fee import Fee
from quantum.domain.shared.errors.invariants import InvariantViolation
from quantum.domain.shared.primitives.value_object import ValueObject
from quantum.domain.shared.value_objects.epoch_ms import EpochMs
from quantum.domain.trading.value_objects.market.price import Price
from quantum.domain.trading.value_objects.market.volume import PositiveVolume


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
