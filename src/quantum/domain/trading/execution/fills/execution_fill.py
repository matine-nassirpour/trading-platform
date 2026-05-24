from dataclasses import dataclass

from quantum.domain.shared_kernel.foundation.errors.invariants import InvariantViolation
from quantum.domain.shared_kernel.modeling.monetary.price import Price
from quantum.domain.shared_kernel.modeling.temporal.epoch_ms import EpochMs
from quantum.domain.shared_kernel.modeling.value_objects.value_object import ValueObject
from quantum.domain.trading.common.value_objects.volume import PositiveVolume
from quantum.domain.trading.execution.fills.execution_id import ExecutionId
from quantum.domain.trading.execution.fills.execution_link import ExecutionLink


@dataclass(frozen=True, slots=True)
class ExecutionFill(ValueObject):
    """
    Atomic economic execution fill.

    Represents WHAT was executed and WHERE it is reconciled broker-side.
    """

    execution_id: ExecutionId
    link: ExecutionLink

    price: Price
    volume: PositiveVolume
    executed_at: EpochMs

    def _validate_semantics(self) -> None:
        required_fields: tuple[tuple[str, object, type[object]], ...] = (
            ("execution_id", self.execution_id, ExecutionId),
            ("link", self.link, ExecutionLink),
            ("price", self.price, Price),
            ("volume", self.volume, PositiveVolume),
            ("executed_at", self.executed_at, EpochMs),
        )

        for field_name, value, expected_type in required_fields:
            if not isinstance(value, expected_type):
                raise InvariantViolation(f"ExecutionFill.{field_name} invalid")
