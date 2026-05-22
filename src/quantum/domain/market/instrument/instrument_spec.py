from dataclasses import dataclass

from quantum.domain.market.instrument.constraints.instrument_constraints import (
    InstrumentConstraints,
)
from quantum.domain.market.instrument.currency.instrument_currencies import (
    InstrumentCurrencies,
)
from quantum.domain.market.instrument.identity.symbol import Symbol
from quantum.domain.market.instrument.microstructure.instrument_microstructure import (
    InstrumentMicrostructure,
)
from quantum.domain.market.instrument.precision.instrument_precision import (
    InstrumentPrecision,
)
from quantum.domain.shared_kernel.foundation.errors.invariants import InvariantViolation
from quantum.domain.shared_kernel.modeling.monetary.money_context import MoneyContext
from quantum.domain.shared_kernel.modeling.value_objects.value_object import ValueObject


@dataclass(frozen=True, slots=True)
class InstrumentSpec(ValueObject):
    symbol: Symbol
    context: MoneyContext

    precision: InstrumentPrecision
    constraints: InstrumentConstraints
    microstructure: InstrumentMicrostructure
    currencies: InstrumentCurrencies

    def _validate_semantics(self) -> None:
        required_fields: tuple[tuple[str, object, type[object]], ...] = (
            ("symbol", self.symbol, Symbol),
            ("context", self.context, MoneyContext),
            ("precision", self.precision, InstrumentPrecision),
            ("constraints", self.constraints, InstrumentConstraints),
            ("microstructure", self.microstructure, InstrumentMicrostructure),
            ("currencies", self.currencies, InstrumentCurrencies),
        )

        for field_name, value, expected_type in required_fields:
            if not isinstance(value, expected_type):
                raise InvariantViolation(
                    f"InstrumentSpec.{field_name} "
                    f"must be {expected_type.__name__}, "
                    f"got {type(value).__name__}"
                )

        if (
            self.microstructure.tick_value.currency
            not in self.context.allowed_currencies
        ):
            raise InvariantViolation(
                "tick_value.currency must belong to MoneyContext.allowed_currencies"
            )

        if self.currencies.pnl_currency not in self.context.allowed_currencies:
            raise InvariantViolation(
                "pnl_currency must belong to MoneyContext.allowed_currencies"
            )
