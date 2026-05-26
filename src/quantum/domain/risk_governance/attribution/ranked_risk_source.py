from dataclasses import dataclass

from quantum.domain.risk_governance.attribution.risk_attribution_rank import (
    RiskAttributionRank,
)
from quantum.domain.risk_governance.attribution.risk_source import RiskSource
from quantum.domain.shared_kernel.foundation.errors.invariants import InvariantViolation
from quantum.domain.shared_kernel.modeling.value_objects.value_object import ValueObject


@dataclass(frozen=True, slots=True)
class RankedRiskSource(ValueObject):
    """
    Risk source with explicit deterministic relevance ordering.
    """

    rank: RiskAttributionRank
    source: RiskSource

    def _validate_semantics(self) -> None:
        if not isinstance(self.rank, RiskAttributionRank):
            raise InvariantViolation("RankedRiskSource.rank invalid")

        if not isinstance(self.source, RiskSource):
            raise InvariantViolation("RankedRiskSource.source invalid")
