from abc import abstractmethod
from typing import Protocol, runtime_checkable

from quantum.domain.market.regime.market_regime import MarketRegime
from quantum.domain.shared_kernel.value_objects.symbol import Symbol


@runtime_checkable
class MarketRegimeProvider(Protocol):
    """
    Provides the current market regime for a given instrument.
    """

    @abstractmethod
    def current_regime(self, symbol: Symbol) -> MarketRegime:
        raise NotImplementedError
