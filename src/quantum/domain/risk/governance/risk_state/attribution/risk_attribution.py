from __future__ import annotations

from dataclasses import dataclass

from quantum.domain.risk.governance.risk_state.attribution.ranked_risk_source import (
    RankedRiskSource,
)
from quantum.domain.risk.governance.risk_state.attribution.risk_attribution_rank import (
    RiskAttributionRank,
)
from quantum.domain.risk.governance.risk_state.attribution.risk_source import RiskSource
from quantum.domain.shared_kernel.foundation.errors.invariants import InvariantViolation
from quantum.domain.shared_kernel.modeling.value_objects.value_object import ValueObject


@dataclass(frozen=True, slots=True)
class RiskAttribution(ValueObject):
    """
    Canonical deterministic attribution of a risk event.

    Sources are ordered explicitly by rank:
    - rank 1 = primary source
    - ranks must be strictly increasing
    - duplicate sources are forbidden
    """

    sources: tuple[RankedRiskSource, ...]

    def _validate_semantics(self) -> None:
        if not isinstance(self.sources, tuple):
            raise InvariantViolation("RiskAttribution.sources must be a tuple")

        if not self.sources:
            raise InvariantViolation("RiskAttribution must contain at least one source")

        previous_rank: int | None = None
        seen_sources: set[RiskSource] = set()

        for ranked_source in self.sources:
            if not isinstance(ranked_source, RankedRiskSource):
                raise InvariantViolation(
                    "RiskAttribution.sources must contain only RankedRiskSource"
                )

            current_rank = ranked_source.rank.value

            if previous_rank is not None and current_rank <= previous_rank:
                raise InvariantViolation(
                    "RiskAttribution ranks must be strictly increasing"
                )

            if ranked_source.source in seen_sources:
                raise InvariantViolation(
                    "RiskAttribution must not contain duplicate RiskSource"
                )

            seen_sources.add(ranked_source.source)
            previous_rank = current_rank

    @staticmethod
    def single(source: RiskSource) -> RiskAttribution:
        return RiskAttribution(
            sources=(
                RankedRiskSource(
                    rank=RiskAttributionRank(1),
                    source=source,
                ),
            )
        )

    @staticmethod
    def ranked(sources: tuple[RiskSource, ...]) -> RiskAttribution:
        if not sources:
            raise InvariantViolation(
                "RiskAttribution.ranked() requires at least one RiskSource"
            )

        for source in sources:
            if not isinstance(source, RiskSource):
                raise InvariantViolation(
                    "RiskAttribution.ranked() requires only RiskSource instances"
                )

        return RiskAttribution(
            sources=tuple(
                RankedRiskSource(
                    rank=RiskAttributionRank(index),
                    source=source,
                )
                for index, source in enumerate(sources, start=1)
            )
        )
