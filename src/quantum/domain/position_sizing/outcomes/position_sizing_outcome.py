from __future__ import annotations

from dataclasses import dataclass

from quantum.domain.position_sizing.model.policies.position_sizing_rejection_reason_code import (
    PositionSizingRejectionReasonCode,
)
from quantum.domain.position_sizing.model.result.position_sizing_result import (
    PositionSizingResult,
)
from quantum.domain.shared_kernel.foundation.errors.invariants import InvariantViolation
from quantum.domain.shared_kernel.modeling.value_objects.value_object import ValueObject


@dataclass(frozen=True, slots=True)
class PositionSizingOutcome(ValueObject):
    """
    Semantic domain outcome of a position sizing evaluation.

    Application handlers must consume this outcome instead of inspecting
    concrete PositionSizing event types.
    """

    sized: bool
    result: PositionSizingResult | None
    rejection_reason: PositionSizingRejectionReasonCode | None

    def _validate_types(self) -> None:
        if type(self.sized) is not bool:
            raise InvariantViolation("PositionSizingOutcome.sized must be bool")

        if self.result is not None and not isinstance(
            self.result, PositionSizingResult
        ):
            raise InvariantViolation(
                "PositionSizingOutcome.result must be PositionSizingResult or None"
            )

        if self.rejection_reason is not None and not isinstance(
            self.rejection_reason,
            PositionSizingRejectionReasonCode,
        ):
            raise InvariantViolation(
                "PositionSizingOutcome.rejection_reason must be "
                "PositionSizingRejectionReasonCode or None"
            )

    def _validate_semantics(self) -> None:
        self._validate_types()

        if self.sized:
            if self.result is None:
                raise InvariantViolation("Sized PositionSizingOutcome requires result")

            if self.rejection_reason is not None:
                raise InvariantViolation(
                    "Sized PositionSizingOutcome must not define rejection_reason"
                )

        else:
            if self.result is not None:
                raise InvariantViolation(
                    "Rejected PositionSizingOutcome must not define result"
                )

            if self.rejection_reason is None:
                raise InvariantViolation(
                    "Rejected PositionSizingOutcome requires rejection_reason"
                )

    @classmethod
    def sized(
        cls,
        *,
        result: PositionSizingResult,
    ) -> PositionSizingOutcome:
        return cls(
            sized=True,
            result=result,
            rejection_reason=None,
        )

    @classmethod
    def rejected(
        cls,
        *,
        rejection_reason: PositionSizingRejectionReasonCode,
    ) -> PositionSizingOutcome:
        return cls(
            sized=False,
            result=None,
            rejection_reason=rejection_reason,
        )
