from dataclasses import dataclass

from quantum.domain.model.value_objects.base import ValueObject


@dataclass(frozen=True)
class OrderRequestSnapshot(ValueObject):
    """
    Canonical, broker-agnostic snapshot of an order request.
    """

    symbol: str
    volume: str
    order_type: str
    sl: str | None = None
    tp: str | None = None

    def _validate(self) -> None:
        if not self.symbol:
            raise ValueError("Symbol required")
        if not self.volume:
            raise ValueError("Volume required")
