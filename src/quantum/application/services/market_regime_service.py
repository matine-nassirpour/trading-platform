from quantum.application.ports.outbound.event_store import EventStore
from quantum.application.ports.outbound.market_regime_provider import (
    MarketRegimeProvider,
)
from quantum.domain.market.regime.market_regime import MarketRegime
from quantum.domain.shared_kernel.value_objects.symbol import Symbol
from quantum.domain.trading.events.v1.governance.market_regime_changed_event import (
    MarketRegimeChangedEvent,
)


class MarketRegimeService:
    """
    Application service for querying market regime semantics.
    """

    def __init__(self, provider: MarketRegimeProvider, event_store: EventStore) -> None:
        self._provider = provider
        self._event_store = event_store

    def is_tradable(self, symbol: Symbol) -> bool:
        regime = self._provider.current_regime(symbol)
        return regime.is_tradable()

    def is_high_risk(self, symbol: Symbol) -> bool:
        regime = self._provider.current_regime(symbol)
        return regime.is_high_risk()

    def publish_change(self, previous: MarketRegime, current: MarketRegime):
        event = MarketRegimeChangedEvent(
            previous=previous,
            current=current,
        )

        self._event_store.append(event)
