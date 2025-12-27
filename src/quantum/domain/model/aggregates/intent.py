from dataclasses import dataclass

from quantum.domain.model.exceptions import InvalidStateTransition
from quantum.domain.model.value_objects.identifiers import IntentId
from quantum.domain.model.value_objects.price import Price
from quantum.domain.model.value_objects.symbol import Symbol
from quantum.domain.model.value_objects.volume import Volume


@dataclass
class TradingIntent:
    """
    Aggregate Root.
    A trading decision, immutable once submitted.
    """

    intent_id: IntentId
    symbol: Symbol
    volume: Volume
    entry_price: Price | None
    sl: Price | None
    tp: Price | None

    _submitted: bool = False

    def submit(self) -> None:
        if self._submitted:
            raise InvalidStateTransition("TradingIntent already submitted")

        if self.volume.value <= 0:
            raise InvalidStateTransition("Volume must be positive")

        self._submitted = True

    @property
    def is_submitted(self) -> bool:
        return self._submitted
