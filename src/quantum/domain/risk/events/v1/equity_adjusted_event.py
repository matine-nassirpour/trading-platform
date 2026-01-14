from dataclasses import dataclass
from typing import ClassVar

from quantum.domain.risk.value_objects.equity import Equity
from quantum.domain.shared_kernel.events.base_event import BaseEvent
from quantum.domain.shared_kernel.value_objects.realized_pnl import RealizedPnL


@dataclass(frozen=True, slots=True)
class EquityAdjustedEvent(BaseEvent):
    """
    Emitted whenever equity is adjusted by a realized PnL.

    This is the SINGLE source of truth for equity evolution.
    """

    event_name: ClassVar[str] = "risk.equity_adjusted"
    event_version: ClassVar[int] = 1

    pnl: RealizedPnL
    new_equity: Equity
    new_equity_peak: Equity
