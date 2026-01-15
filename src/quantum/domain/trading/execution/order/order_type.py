from dataclasses import dataclass
from typing import ClassVar

from quantum.domain.shared_kernel.primitives.closed_set_value_object import (
    ClosedSetValueObject,
)


@dataclass(frozen=True, slots=True)
class OrderType(ClosedSetValueObject):
    _ALLOWED_VALUES: ClassVar[frozenset[str]] = frozenset(
        {
            "buy",
            "sell",
            "buy_limit",
            "sell_limit",
            "buy_stop",
            "sell_stop",
            "buy_stop_limit",
            "sell_stop_limit",
            "close_by",
        }
    )

    # --- Semantic helpers -----------------------------------------------------

    def requires_limit_price(self) -> bool:
        return self.value in {
            "buy_limit",
            "sell_limit",
            "buy_stop_limit",
            "sell_stop_limit",
        }

    def requires_stop_price(self) -> bool:
        return self.value in {
            "buy_stop",
            "sell_stop",
            "buy_stop_limit",
            "sell_stop_limit",
        }

    def forbids_limit_price(self) -> bool:
        return self.value in {
            "buy",
            "sell",
            "buy_stop",
            "sell_stop",
        }

    def forbids_stop_price(self) -> bool:
        return self.value in {
            "buy",
            "sell",
            "buy_limit",
            "sell_limit",
        }

    def requires_price_reference(self) -> bool:
        return self.value not in {
            "buy",
            "sell",
        }
