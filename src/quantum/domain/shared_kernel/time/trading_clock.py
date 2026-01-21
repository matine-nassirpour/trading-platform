from dataclasses import dataclass
from datetime import UTC, datetime

from quantum.domain.shared_kernel.errors.invariants import InvariantViolation
from quantum.domain.shared_kernel.value_objects.epoch_ms import EpochMs


@dataclass(frozen=True, slots=True)
class TradingClock:
    """
    Canonical trading clock.

    Provides:
    - deterministic time abstraction
    - testability
    - domain-safe access to current time
    """

    @staticmethod
    def now_utc() -> EpochMs:
        """
        Returns current UTC time as EpochMs.
        """
        now = datetime.now(tz=UTC)
        return EpochMs.from_datetime(now)

    @staticmethod
    def from_datetime(dt: datetime) -> EpochMs:
        if not isinstance(dt, datetime):
            raise InvariantViolation("TradingClock expects datetime")

        if dt.tzinfo is None:
            raise InvariantViolation("Datetime must be timezone-aware")

        return EpochMs.from_datetime(dt)
