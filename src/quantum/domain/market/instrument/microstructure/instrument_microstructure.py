from dataclasses import dataclass

from quantum.domain.market.instrument.microstructure.contract_size import ContractSize
from quantum.domain.market.instrument.microstructure.pip_size import PipSize
from quantum.domain.market.instrument.microstructure.point_size import PointSize
from quantum.domain.market.instrument.microstructure.point_value import PointValue
from quantum.domain.market.instrument.microstructure.tick_size import TickSize
from quantum.domain.market.instrument.microstructure.tick_value import TickValue
from quantum.domain.shared_kernel.foundation.errors.invariants import InvariantViolation
from quantum.domain.shared_kernel.modeling.value_objects.value_object import ValueObject


@dataclass(frozen=True, slots=True)
class InstrumentMicrostructure(ValueObject):
    """
    Canonical executable price/contract microstructure.

    Definitions:
    - tick_size   : minimum executable price increment
    - tick_value  : monetary value of one tick
    - point_size  : canonical point increment
    - point_value : monetary value of one point
    - pip_size    : optional FX pip increment
    """

    contract_size: ContractSize
    tick_size: TickSize
    tick_value: TickValue
    point_size: PointSize
    point_value: PointValue
    pip_size: PipSize | None = None

    def _validate_types(self) -> None:
        required_fields: tuple[tuple[str, object, type[object]], ...] = (
            ("contract_size", self.contract_size, ContractSize),
            ("tick_size", self.tick_size, TickSize),
            ("tick_value", self.tick_value, TickValue),
            ("point_size", self.point_size, PointSize),
            ("point_value", self.point_value, PointValue),
        )

        for field_name, value, expected_type in required_fields:
            if not isinstance(value, expected_type):
                raise InvariantViolation(
                    f"InstrumentMicrostructure.{field_name} "
                    f"must be {expected_type.__name__}, "
                    f"got {type(value).__name__}"
                )

    def _validate_semantics(self) -> None:
        self._validate_types()

        if self.pip_size is not None and not isinstance(self.pip_size, PipSize):
            raise InvariantViolation("pip_size must be PipSize or None")

        if self.tick_value.currency != self.point_value.currency:
            raise InvariantViolation(
                "tick_value.currency and point_value.currency must match"
            )

        ratio = self.point_size.value / self.tick_size.value

        if ratio != ratio.to_integral_value():
            raise InvariantViolation(
                "point_size must be an exact multiple of tick_size"
            )

        expected_point_value = self.tick_value.value * ratio

        if self.point_value.value != expected_point_value:
            raise InvariantViolation(
                "point_value must equal tick_value * (point_size / tick_size)"
            )

        if self.pip_size is not None:
            pip_ratio = self.pip_size.value / self.tick_size.value

            if pip_ratio != pip_ratio.to_integral_value():
                raise InvariantViolation(
                    "pip_size must be an exact multiple of tick_size"
                )
