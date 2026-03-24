from dataclasses import dataclass
from datetime import date

from quantum.domain.market.temporal.market_session import MarketSession
from quantum.domain.market.temporal.utc_minute import UtcMinuteOfDay
from quantum.domain.shared_kernel.ddd.value_objects.value_object import ValueObject
from quantum.domain.shared_kernel.foundation.errors.invariants import InvariantViolation
from quantum.domain.shared_kernel.temporal.epoch_ms import EpochMs


@dataclass(frozen=True, slots=True)
class TradingCalendar(ValueObject):
    """
    Canonical trading calendar.

    Defines:
    - which days are tradable
    - which sessions are active
    - whether trading is allowed at a given time
    """

    name: str
    sessions: tuple[MarketSession, ...]
    holidays: frozenset[date]

    def _validate_semantics(self) -> None:
        if not self.name:
            raise InvariantViolation("TradingCalendar requires a name")

        if not self.sessions:
            raise InvariantViolation("At least one MarketSession is required")

        for s in self.sessions:
            if not isinstance(s, MarketSession):
                raise InvariantViolation("Invalid MarketSession")

        for h in self.holidays:
            if not isinstance(h, date):
                raise InvariantViolation("Invalid holiday")

    def is_trading_day(self, d: date) -> bool:
        """
        Returns True if the date is a valid trading day.
        """
        if d.weekday() >= 5:  # Saturday / Sunday
            return False

        if d in self.holidays:
            return False

        return True

    def is_market_open(self, at: EpochMs) -> bool:
        """
        Returns True if market is open at given time.
        """
        dt = at.to_datetime()
        day = dt.date()

        if not self.is_trading_day(day):
            return False

        minute = UtcMinuteOfDay.from_epoch(at)

        return any(session.contains(minute) for session in self.sessions)

    def assert_market_open(self, at: EpochMs) -> None:
        if not self.is_market_open(at):
            raise InvariantViolation("Market is closed at this time")
