from __future__ import annotations

import re

from dataclasses import dataclass

from quantum.domain.shared_kernel.foundation.errors.invariants import InvariantViolation
from quantum.domain.shared_kernel.modeling.value_objects.value_object import ValueObject

_RISK_REFERENCE_RE = re.compile(
    r"^(?P<namespace>[a-z][a-z0-9_-]{0,31}):"
    r"(?P<identifier>[a-z0-9]+(?:[._-][a-z0-9]+)*)$"
)


@dataclass(frozen=True, slots=True)
class RiskReference(ValueObject):
    """
    Canonical opaque identifier for a risk source.

    Format:
        <namespace>:<identifier>

    Examples:
        strategy:mean_reversion_v3
        symbol:eurusd
        position:42
        portfolio:global
        session:london
        external:macro_news
    """

    value: str

    def _validate_semantics(self) -> None:
        if not isinstance(self.value, str):
            raise InvariantViolation("RiskReference must be a string")

        canonical = self.value.strip().lower()

        if not canonical:
            raise InvariantViolation("RiskReference must not be empty")

        if self.value != canonical:
            raise InvariantViolation(
                f"RiskReference must already be canonical. "
                f"Got {self.value!r}, expected {canonical!r}. "
                "Normalization must happen outside the domain."
            )

        if any(ch.isspace() for ch in self.value):
            raise InvariantViolation("RiskReference must not contain whitespace")

        if _RISK_REFERENCE_RE.fullmatch(self.value) is None:
            raise InvariantViolation(
                "RiskReference must match '<namespace>:<identifier>' "
                "with lowercase canonical form and no empty segments"
            )

    def namespace(self) -> str:
        return self.value.split(":", 1)[0]

    def identifier(self) -> str:
        return self.value.split(":", 1)[1]

    def __str__(self) -> str:
        return self.value

    @staticmethod
    def strategy(strategy_id: str) -> RiskReference:
        return RiskReference(f"strategy:{strategy_id}")

    @staticmethod
    def symbol(symbol: str) -> RiskReference:
        return RiskReference(f"symbol:{symbol.lower()}")

    @staticmethod
    def position(position_id: str) -> RiskReference:
        return RiskReference(f"position:{position_id}")

    @staticmethod
    def portfolio(portfolio_id: str) -> RiskReference:
        return RiskReference(f"portfolio:{portfolio_id}")

    @staticmethod
    def session(session_id: str) -> RiskReference:
        return RiskReference(f"session:{session_id}")

    @staticmethod
    def external(reference_id: str) -> RiskReference:
        return RiskReference(f"external:{reference_id}")
