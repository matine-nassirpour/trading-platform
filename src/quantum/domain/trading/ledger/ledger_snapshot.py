from dataclasses import dataclass
from decimal import Decimal

from quantum.domain.shared_kernel.errors.invariants import InvariantViolation
from quantum.domain.trading.ledger.cash_entry import CashEntry
from quantum.domain.trading.ledger.fee_entry import FeeEntry
from quantum.domain.trading.ledger.pnl_entry import PnLEntry


@dataclass(frozen=True, slots=True)
class LedgerSnapshot:
    """
    Immutable financial snapshot.

    Represents the consolidated financial state at a point in time.
    """

    cash: CashEntry
    pnl: PnLEntry
    fees: FeeEntry

    def _validate(self) -> None:
        if not isinstance(self.cash, CashEntry):
            raise InvariantViolation("LedgerSnapshot requires CashEntry")

        if not isinstance(self.pnl, PnLEntry):
            raise InvariantViolation("LedgerSnapshot requires PnLEntry")

        if not isinstance(self.fees, FeeEntry):
            raise InvariantViolation("LedgerSnapshot requires FeeEntry")

    @property
    def equity(self) -> Decimal:
        """
        Equity = Cash + PnL - Fees
        """
        return self.cash.value + self.pnl.value - self.fees.value
