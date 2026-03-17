from __future__ import annotations

from dataclasses import dataclass

from quantum.domain.shared_kernel.primitives.closed_set_value_object import (
    ClosedSetValueObject,
)


@dataclass(frozen=True, slots=True)
class RiskSourceType(ClosedSetValueObject):
    """
    High-level category of risk origin.
    """

    @classmethod
    def _allowed_values(cls) -> frozenset[str]:
        return frozenset(
            {
                "strategy",  # trading logic
                "instrument",  # specific market / symbol
                "position",  # individual position
                "portfolio",  # aggregate exposure
                "session",  # market session / rollover
                "external",  # news, broker, infra
                "unknown",  # explicit fallback
            }
        )

    # --- Named constructors ---------------------------------------------------

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
