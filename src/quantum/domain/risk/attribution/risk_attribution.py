from __future__ import annotations

from dataclasses import dataclass

from quantum.domain.risk.attribution.risk_source import RiskSource
from quantum.domain.shared.errors.invariants import InvariantViolation
from quantum.domain.shared.primitives.value_object import ValueObject


@dataclass(frozen=True)
class RiskAttribution(ValueObject):
    """
    Canonical attribution of a risk event.

    Allows multiple contributing sources, ordered by relevance.
    """

    sources: tuple[RiskSource, ...]

    def _validate(self) -> None:
        if not isinstance(self.sources, tuple):
            raise InvariantViolation("RiskAttribution sources must be a tuple")

        if not self.sources:
            raise InvariantViolation("RiskAttribution must contain at least one source")

        for source in self.sources:
            if not isinstance(source, RiskSource):
                raise InvariantViolation("Invalid RiskSource in attribution")

    @staticmethod
    def single(source: RiskSource) -> RiskAttribution:
        return RiskAttribution((source,))
