from abc import ABC, abstractmethod

from quantum.domain.market.regime.market_regime import MarketRegime
from quantum.domain.shared_kernel.value_objects.symbol import Symbol


class MarketRegimeProvider(ABC):
    """
    Provides the current market regime for a given instrument.
    """

    @abstractmethod
    def current_regime(self, symbol: Symbol) -> MarketRegime:
        raise NotImplementedError
