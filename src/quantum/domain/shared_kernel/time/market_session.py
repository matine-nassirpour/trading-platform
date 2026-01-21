from dataclasses import dataclass
from datetime import time

from quantum.domain.shared_kernel.errors.invariants import InvariantViolation
from quantum.domain.shared_kernel.primitives.value_object import ValueObject


@dataclass(frozen=True, slots=True)
class MarketSession(ValueObject):
    """
    Represents a recurring market session.

    Example:
        London: 08:00 → 17:00 UTC
    """

    name: str
    opens_at: time
    closes_at: time

    def _validate(self) -> None:
        if not self.name or not isinstance(self.name, str):
            raise InvariantViolation("MarketSession requires a name")

        if not isinstance(self.opens_at, time):
            raise InvariantViolation("opens_at must be a time")

        if not isinstance(self.closes_at, time):
            raise InvariantViolation("closes_at must be a time")

        if self.opens_at == self.closes_at:
            raise InvariantViolation("Session cannot open and close at same time")

    def contains(self, t: time) -> bool:
        """
        Returns True if the given time falls inside the session.
        Supports overnight sessions.
        """
        if self.opens_at < self.closes_at:
            return self.opens_at <= t < self.closes_at
        else:
            # Overnight session
            return t >= self.opens_at or t < self.closes_at
