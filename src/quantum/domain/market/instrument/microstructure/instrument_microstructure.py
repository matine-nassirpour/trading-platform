from dataclasses import dataclass

from quantum.domain.market.instrument.microstructure.contract_size import ContractSize
from quantum.domain.market.instrument.microstructure.tick_value import TickValue
from quantum.domain.shared_kernel.foundation.errors.invariants import InvariantViolation
from quantum.domain.shared_kernel.modeling.value_objects.value_object import ValueObject


@dataclass(frozen=True, slots=True)
class InstrumentMicrostructure(ValueObject):
    contract_size: ContractSize
    tick_value: TickValue

    def _validate_semantics(self) -> None:
        if not isinstance(self.contract_size, ContractSize):
            raise InvariantViolation("contract_size must be ContractSize")

        if not isinstance(self.tick_value, TickValue):
            raise InvariantViolation("tick_value must be TickValue")
