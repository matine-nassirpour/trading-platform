from typing import Protocol, runtime_checkable

from quantum.domain.shared_kernel.identifiers.intent_id import IntentId
from quantum.domain.trading.intent.trading_intent import TradingIntent


@runtime_checkable
class TradingIntentRepository(Protocol):
    """
    Persistence port for TradingIntent aggregate.
    """

    def load(self, intent_id: IntentId) -> TradingIntent:
        raise NotImplementedError

    def save(self, intent: TradingIntent) -> None:
        raise NotImplementedError
