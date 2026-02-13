from collections.abc import Iterable
from typing import Protocol, runtime_checkable

from quantum.domain.market.instrument.instrument_spec import InstrumentSpec
from quantum.domain.shared_kernel.value_objects.symbol import Symbol


@runtime_checkable
class InstrumentSpecProvider(Protocol):
    """
    Provides broker-aligned instrument specifications to the application layer.

    This is not "market data"; it's reference data required for pricing/risk invariants.
    Implementations might source from broker/terminal metadata, cache, DB, etc.
    """

    def get(self, symbol: Symbol) -> InstrumentSpec:
        """
        Must raise a domain-meaningful exception at application boundary
        (e.g., application error) if symbol is unknown/unavailable.
        """
        raise NotImplementedError

    def list_all(self) -> Iterable[InstrumentSpec]:
        raise NotImplementedError
