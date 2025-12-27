from __future__ import annotations

from dataclasses import dataclass, replace

from quantum.domain.model.aggregates.base import AggregateRoot
from quantum.domain.model.exceptions import InvalidStateTransition
from quantum.domain.model.value_objects.identifiers import IntentId
from quantum.domain.model.value_objects.price import Price
from quantum.domain.model.value_objects.symbol import Symbol
from quantum.domain.model.value_objects.volume import Volume


@dataclass(frozen=True)
class TradingIntent(AggregateRoot):
    """
    Aggregate Root.
    Immutable trading intent.
    """

    intent_id: IntentId
    symbol: Symbol
    volume: Volume
    entry_price: Price | None
    sl: Price | None
    tp: Price | None
    submitted: bool = False

    def submit(self) -> TradingIntent:
        if self.submitted:
            raise InvalidStateTransition("TradingIntent already submitted")

        return replace(self, submitted=True)
