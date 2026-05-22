from __future__ import annotations

from dataclasses import dataclass

from quantum.domain.shared_kernel.modeling.value_objects.closed_set_value_object import (
    ClosedSetValueObject,
)


@dataclass(frozen=True, slots=True)
class OrderKind(ClosedSetValueObject):
    """
    Canonical order execution kind.
    """

    @classmethod
    def _allowed_values(cls) -> frozenset[str]:
        return frozenset(
            {
                "market",
                "limit",
                "stop",
                "stop_limit",
                "close_by",
            }
        )

    @classmethod
    def market(cls) -> OrderKind:
        return cls("market")

    @classmethod
    def limit(cls) -> OrderKind:
        return cls("limit")

    @classmethod
    def stop(cls) -> OrderKind:
        return cls("stop")

    @classmethod
    def stop_limit(cls) -> OrderKind:
        return cls("stop_limit")

    @classmethod
    def close_by(cls) -> OrderKind:
        return cls("close_by")

    # --- Semantic helpers -----------------------------------------------------

    def requires_limit_price(self) -> bool:
        return self.value in {"limit", "stop_limit"}

    def requires_stop_price(self) -> bool:
        return self.value in {"stop", "stop_limit"}

    def forbids_limit_price(self) -> bool:
        return self.value in {"market", "stop", "close_by"}

    def forbids_stop_price(self) -> bool:
        return self.value in {"market", "limit", "close_by"}

    def requires_price_reference(self) -> bool:
        return self.value in {"limit", "stop", "stop_limit"}
