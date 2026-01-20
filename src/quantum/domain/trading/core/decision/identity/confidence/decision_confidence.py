from dataclasses import dataclass

from quantum.domain.shared_kernel.errors.invariants import InvariantViolation
from quantum.domain.shared_kernel.primitives.value_object import ValueObject
from quantum.domain.trading.core.decision.identity.confidence.decision_confidence_level import (
    DecisionConfidenceLevel,
)


@dataclass(frozen=True, slots=True)
class DecisionConfidence(ValueObject):
    """
    Canonical Decision Confidence Envelope.

    This object answers:
        "How confident was the system in THIS decision?"

    Properties:
    - Declarative
    - Non-metric
    - Non-computable
    - Explicitly provided by the decision logic
    """

    level: DecisionConfidenceLevel
    rationale: str | None = None

    def _validate(self) -> None:
        if not isinstance(self.level, DecisionConfidenceLevel):
            raise InvariantViolation("DecisionConfidence requires a valid level")

        if self.rationale is not None:
            if not isinstance(self.rationale, str) or not self.rationale.strip():
                raise InvariantViolation(
                    "DecisionConfidence rationale must be a non-empty string"
                )
