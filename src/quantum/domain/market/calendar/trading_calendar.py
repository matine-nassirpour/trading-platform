from dataclasses import dataclass

from quantum.domain.market.calendar.market_session import MarketSession
from quantum.domain.market.calendar.utc_date import UtcDate
from quantum.domain.market.calendar.utc_minute import UtcMinuteOfDay
from quantum.domain.shared_kernel.foundation.errors.invariants import InvariantViolation
from quantum.domain.shared_kernel.modeling.temporal.epoch_ms import EpochMs
from quantum.domain.shared_kernel.modeling.value_objects.value_object import ValueObject


@dataclass(frozen=True, slots=True)
class TradingCalendar(ValueObject):
    """
    Canonical trading calendar.

    Defines:
    - which UTC dates are tradable
    - which sessions are active
    - whether trading is allowed at a given UTC timestamp
    """

    name: str
    sessions: tuple[MarketSession, ...]
    holidays: tuple[UtcDate, ...]

    @staticmethod
    def _validate_canonical_calendar_name(name: str) -> None:
        if not isinstance(name, str):
            raise InvariantViolation("TradingCalendar.name must be a string")

        canonical_name = name.strip().lower()

        if not canonical_name:
            raise InvariantViolation("TradingCalendar.name must not be empty")

        if name != canonical_name:
            raise InvariantViolation(
                f"TradingCalendar.name must already be canonical. "
                f"Got {name!r}, expected {canonical_name!r}. "
                "Normalization must happen outside the domain."
            )

    @staticmethod
    def _validate_sessions(sessions: tuple[MarketSession, ...]) -> None:
        if not isinstance(sessions, tuple):
            raise InvariantViolation("TradingCalendar.sessions must be a tuple")

        if not sessions:
            raise InvariantViolation("At least one MarketSession is required")

        for session in sessions:
            if not isinstance(session, MarketSession):
                raise InvariantViolation(
                    "TradingCalendar.sessions must contain only MarketSession"
                )

    @staticmethod
    def _date_key(day: UtcDate) -> tuple[int, int, int]:
        return day.year, day.month, day.day

    @classmethod
    def _validate_holidays(cls, holidays: tuple[UtcDate, ...]) -> None:
        if not isinstance(holidays, tuple):
            raise InvariantViolation(
                "TradingCalendar.holidays must be a tuple[UtcDate, ...]"
            )

        previous_key: tuple[int, int, int] | None = None

        for holiday in holidays:
            if not isinstance(holiday, UtcDate):
                raise InvariantViolation(
                    "TradingCalendar.holidays must contain only UtcDate"
                )

            current_key = cls._date_key(holiday)

            if previous_key is not None and current_key <= previous_key:
                raise InvariantViolation(
                    "TradingCalendar.holidays must be strictly sorted by UTC date "
                    "and must not contain duplicates"
                )

            previous_key = current_key

    def _validate_semantics(self) -> None:
        self._validate_canonical_calendar_name(self.name)
        self._validate_sessions(self.sessions)
        self._validate_holidays(self.holidays)

    def is_trading_day(self, day: UtcDate) -> bool:
        """
        Returns True if the date is a valid trading day.
        """

        if day.weekday() >= 5:  # Saturday / Sunday
            return False

        if day in self.holidays:
            return False

        return True

    def is_market_open(self, at: EpochMs) -> bool:
        """
        Returns True if market is open at given time.
        """

        day = UtcDate.from_epoch(at)

        if not self.is_trading_day(day):
            return False

        minute = UtcMinuteOfDay.from_epoch(at)

        return any(session.contains(minute) for session in self.sessions)

    def assert_market_open(self, at: EpochMs) -> None:
        if not self.is_market_open(at):
            raise InvariantViolation("Market is closed at this time")
