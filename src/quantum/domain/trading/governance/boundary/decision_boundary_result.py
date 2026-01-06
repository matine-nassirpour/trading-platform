from dataclasses import dataclass

from quantum.domain.shared_kernel.primitives.value_object import ValueObject


@dataclass(frozen=True)
class DecisionBoundaryResult(ValueObject):
    """
    Result of a DecisionBoundary evaluation.

    Explicit and replayable.
    """

    authorized: bool
    reason: str

    def _validate(self) -> None:
        if not isinstance(self.authorized, bool):
            raise ValueError("authorized must be a boolean")

        if not isinstance(self.reason, str) or not self.reason.strip():
            raise ValueError("DecisionBoundaryResult requires a non-empty reason")
