from __future__ import annotations

from dataclasses import dataclass

from quantum.domain.risk.governance.risk_state.attribution.risk_source import RiskSource
from quantum.domain.shared_kernel.foundation.errors.invariants import InvariantViolation
from quantum.domain.shared_kernel.modeling.value_objects.value_object import ValueObject


@dataclass(frozen=True, slots=True)
class RiskAttribution(ValueObject):
    """
    Canonical attribution of a risk event.

    Allows multiple contributing sources, ordered by relevance.
    """

    sources: tuple[RiskSource, ...]

    def _validate_semantics(self) -> None:
        if not self.sources:
            raise InvariantViolation("RiskAttribution must contain at least one source")

        for source in self.sources:
            if not isinstance(source, RiskSource):
                raise InvariantViolation(
                    f"Invalid RiskSource in attribution: {source!r}"
                )

    @staticmethod
    def single(source: RiskSource) -> RiskAttribution:
        return RiskAttribution((source,))
