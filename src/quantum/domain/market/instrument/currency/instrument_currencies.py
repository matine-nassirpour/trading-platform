from dataclasses import dataclass

from quantum.domain.market.instrument.currency.currency_pair import CurrencyPair
from quantum.domain.shared_kernel.foundation.errors.invariants import InvariantViolation
from quantum.domain.shared_kernel.modeling.monetary.currency import Currency
from quantum.domain.shared_kernel.modeling.value_objects.value_object import ValueObject


@dataclass(frozen=True, slots=True)
class InstrumentCurrencies(ValueObject):
    pair: CurrencyPair
    pnl_currency: Currency

    def _validate_semantics(self) -> None:
        if not isinstance(self.pair, CurrencyPair):
            raise InvariantViolation("InstrumentCurrencies.pair must be CurrencyPair")

        if not isinstance(self.pnl_currency, Currency):
            raise InvariantViolation(
                "InstrumentCurrencies.pnl_currency must be Currency"
            )

        if self.pnl_currency not in (self.pair.base, self.pair.quote):
            raise InvariantViolation(
                "pnl_currency must be either base or quote currency"
            )
