from __future__ import annotations

from typing import ClassVar

from quantum.domain.shared.primitives.closed_set_value_object import (
    ClosedSetValueObject,
)


class RiskSourceType(ClosedSetValueObject):
    """
    High-level category of risk origin.
    """

    _ALLOWED_VALUES: ClassVar[frozenset[str]] = frozenset(
        {
            "strategy",  # trading logic
            "instrument",  # specific market / symbol
            "position",  # individual position
            "portfolio",  # aggregate exposure
            "session",  # market session / rollover
            "external",  # news, broker, infra
            "unknown",  # fallback (must be explicit)
        }
    )

    @classmethod
    def strategy(cls) -> RiskSourceType:
        return cls("strategy")

    @classmethod
    def instrument(cls) -> RiskSourceType:
        return cls("instrument")

    @classmethod
    def position(cls) -> RiskSourceType:
        return cls("position")

    @classmethod
    def portfolio(cls) -> RiskSourceType:
        return cls("portfolio")

    @classmethod
    def session(cls) -> RiskSourceType:
        return cls("session")

    @classmethod
    def external(cls) -> RiskSourceType:
        return cls("external")

    @classmethod
    def unknown(cls) -> RiskSourceType:
        return cls("unknown")
