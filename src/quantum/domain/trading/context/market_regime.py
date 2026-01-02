from __future__ import annotations

from typing import ClassVar

from quantum.domain.shared.primitives.closed_set_value_object import (
    ClosedSetValueObject,
)


class MarketRegime(ClosedSetValueObject):
    """
    Canonical market regime.

    Describes the CURRENT structural state of the market,
    independent of any specific strategy.
    """

    _ALLOWED_VALUES: ClassVar[frozenset[str]] = frozenset(
        {
            "normal",  # default, liquid, continuous
            "volatile",  # high variance, unstable prices
            "illiquid",  # poor liquidity, wide spreads
            "news",  # macro/news-driven instability
            "closed",  # market closed / rollover
        }
    )

    # --- Named constructors --------------------------------------------------

    @classmethod
    def normal(cls) -> MarketRegime:
        return cls("normal")

    @classmethod
    def volatile(cls) -> MarketRegime:
        return cls("volatile")

    @classmethod
    def illiquid(cls) -> MarketRegime:
        return cls("illiquid")

    @classmethod
    def news(cls) -> MarketRegime:
        return cls("news")

    @classmethod
    def closed(cls) -> MarketRegime:
        return cls("closed")

    # --- Semantic helpers ----------------------------------------------------

    def is_tradable(self) -> bool:
        return self.value not in {"closed"}

    def is_high_risk(self) -> bool:
        return self.value in {"volatile", "news", "illiquid"}
