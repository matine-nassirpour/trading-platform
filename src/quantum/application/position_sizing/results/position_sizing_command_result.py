from dataclasses import dataclass

from quantum.domain.position_sizing.model.policies.position_sizing_rejection_reason_code import (
    PositionSizingRejectionReasonCode,
)
from quantum.domain.position_sizing.model.result.position_sizing_result import (
    PositionSizingResult,
)
from quantum.domain.position_sizing.position_sizing_id import PositionSizingId


@dataclass(frozen=True, slots=True)
class PositionSizingCommandResult:
    """
    Base application result for commands targeting PositionSizing.
    """

    sizing_id: PositionSizingId


@dataclass(frozen=True, slots=True)
class RequestPositionSizingResult(PositionSizingCommandResult):
    """
    Result for position sizing request workflow.
    """


@dataclass(frozen=True, slots=True)
class PerformPositionSizingResult(PositionSizingCommandResult):
    """
    Result for position sizing evaluation workflow.

    The persisted domain event remains the source of truth.
    This result exists as an application convenience for downstream orchestration.
    """

    sized: bool
    result: PositionSizingResult | None
    rejection_reason: PositionSizingRejectionReasonCode | None
