from dataclasses import dataclass

from quantum.domain.shared_kernel.modeling.monetary.pnl import RealizedPnL
from quantum.domain.trading.position.aggregate import PositionId


@dataclass(frozen=True, slots=True)
class PositionCommandResult:
    """
    Base application result for commands targeting Position.
    """

    position_id: PositionId


@dataclass(frozen=True, slots=True)
class OpenPositionResult(PositionCommandResult):
    """
    Result for position opening workflow.
    """


@dataclass(frozen=True, slots=True)
class ClosePositionResult(PositionCommandResult):
    """
    Result for position closing workflow.

    The realized PnL is exposed for downstream orchestration, while the persisted
    PositionClosedEvent remains the source of truth.
    """

    realized_pnl: RealizedPnL
