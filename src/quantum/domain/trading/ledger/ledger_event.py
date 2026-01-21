from dataclasses import dataclass
from typing import ClassVar

from quantum.domain.shared_kernel.events.base_event import BaseEvent
from quantum.domain.trading.ledger.cash_entry import CashEntry
from quantum.domain.trading.ledger.fee_entry import FeeEntry
from quantum.domain.trading.ledger.pnl_entry import PnLEntry


@dataclass(frozen=True, slots=True)
class LedgerEvent(BaseEvent):
    """
    Canonical ledger mutation event.

    This is the ONLY way financial state evolves.
    """

    event_name: ClassVar[str] = "trading.ledger.updated"
    event_version: ClassVar[int] = 1

    cash: CashEntry | None = None
    pnl: PnLEntry | None = None
    fee: FeeEntry | None = None
