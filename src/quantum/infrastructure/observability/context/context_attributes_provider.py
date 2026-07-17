from collections.abc import Mapping
from dataclasses import dataclass

from quantum.infrastructure.observability.context.correlation_id import (
    get_correlation_id,
)
from quantum.infrastructure.observability.context.run_id import get_run_id


@dataclass(frozen=True)
class ContextAttributes:
    """
    Immutable snapshot of correlation context.

    This object is intentionally simple:
      - No logic
      - No lazy evaluation
      - Serializable
      - Safe to embed into logs/spans without side effects
    """

    run_id: str | None
    correlation_id: str | None

    def as_dict(self) -> Mapping[str, str]:
        """
        Returns a stable dictionary representation.
        Missing values are omitted, not represented as None.
        """
        out: dict[str, str] = {}
        if self.run_id:
            out["run_id"] = self.run_id
        if self.correlation_id:
            out["correlation_id"] = self.correlation_id
        return out


class ContextAttributesProvider:
    """
    **C0 Pure Provider** of correlation context.

    Industry-grade architecture principles:
        - ZERO dependency on logging or tracing pipelines.
        - Pure read-only data access.
        - No caching (always fresh context).
        - Deterministic, fully testable.
        - Used symmetrically by:
            • Logging pipeline's CorrelationStep
            • Tracing pipeline's _ContextEnricherProcessor
    """

    @staticmethod
    def get() -> ContextAttributes:
        """
        Returns a fresh immutable snapshot of the entire correlation state.
        - Safe to call from ANY thread
        - No global mutation
        - No side effects
        """
        return ContextAttributes(
            run_id=get_run_id(),
            correlation_id=get_correlation_id(),
        )
