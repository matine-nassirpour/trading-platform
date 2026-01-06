from __future__ import annotations

from typing import Protocol, runtime_checkable

from quantum.domain.trading.execution.intent.trading_intent import TradingIntent
from quantum.domain.trading.value_objects.identifiers.intent_id import IntentId


@runtime_checkable
class TradingIntentRepository(Protocol):
    """
    Persistence port for TradingIntent aggregate.

    Contract:
    - get() returns None if not found
    - save() is an upsert
    - implementations MUST ensure optimistic concurrency (versioning) or equivalent safety
    """

    def get(self, intent_id: IntentId) -> TradingIntent | None:
        raise NotImplementedError

    def save(self, intent: TradingIntent) -> None:
        raise NotImplementedError
