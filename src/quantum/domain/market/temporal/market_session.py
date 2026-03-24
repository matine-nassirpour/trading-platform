from dataclasses import dataclass

from quantum.domain.market.temporal.utc_minute import UtcMinuteOfDay
from quantum.domain.shared_kernel.ddd.value_objects.value_object import ValueObject
from quantum.domain.shared_kernel.foundation.errors.invariants import InvariantViolation


@dataclass(frozen=True, slots=True)
class MarketSession(ValueObject):
    """
    Represents a recurring market session.

    Example:
        London: 08:00 → 17:00 UTC
    """

    name: str
    opens_at: UtcMinuteOfDay
    closes_at: UtcMinuteOfDay

    def _validate_semantics(self) -> None:
        if not self.name or not isinstance(self.name, str):
            raise InvariantViolation("MarketSession requires a name")

        if not isinstance(self.opens_at, UtcMinuteOfDay):
            raise InvariantViolation("opens_at must be UtcMinuteOfDay")

        if not isinstance(self.closes_at, UtcMinuteOfDay):
            raise InvariantViolation("closes_at must be UtcMinuteOfDay")

        if self.opens_at.value == self.closes_at.value:
            raise InvariantViolation("Session cannot open and close at same minute")

    def contains(self, minute: UtcMinuteOfDay) -> bool:
        """
        Supports overnight sessions.
        """
        if not isinstance(minute, UtcMinuteOfDay):
            raise InvariantViolation("minute must be UtcMinuteOfDay")

        start = self.opens_at.value
        end = self.closes_at.value
        t = minute.value

        if start < end:
            return start <= t < end
        else:
            # Overnight session (e.g. 22:00 → 05:00)
            return t >= start or t < end
