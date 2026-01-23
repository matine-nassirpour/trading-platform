from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from quantum.domain.shared_kernel.errors.invariants import InvariantViolation
from quantum.domain.shared_kernel.primitives.value_object import ValueObject

_EPOCH_UTC = datetime(1970, 1, 1, tzinfo=UTC)
_SECONDS_PER_DAY = 86_400
_MILLISECONDS_PER_SECOND = 1_000
_MILLISECONDS_PER_DAY = _SECONDS_PER_DAY * _MILLISECONDS_PER_SECOND


@dataclass(frozen=True, slots=True)
class EpochMs(ValueObject):
    """
    Milliseconds since Unix epoch (UTC).

    Guarantees:
    - Integer-only representation
    - No floating-point arithmetic
    - Deterministic and platform-independent
    """

    value: int

    def _validate(self) -> None:
        if not isinstance(self.value, int):
            raise InvariantViolation("EpochMs must be an integer")

        if self.value < 0:
            raise InvariantViolation("EpochMs must be non-negative")

    # --- Conversions ----------------------------------------------------------

    def to_datetime(self) -> datetime:
        """
        Converts this EpochMs to a timezone-aware UTC datetime.

        Guaranteed:
        - tzinfo = UTC
        - No floating point arithmetic
        """
        seconds, millis = divmod(self.value, _MILLISECONDS_PER_SECOND)

        return _EPOCH_UTC + timedelta(
            seconds=seconds,
            milliseconds=millis,
        )

    def to_utc_minute(self) -> int:
        """
        Returns the UTC minute-of-day [0..1439].

        Used for:
        - market sessions
        - trading calendars
        - deterministic temporal logic
        """
        return (self.value // _MILLISECONDS_PER_SECOND) % _SECONDS_PER_DAY // 60

    def to_utc_second(self) -> int:
        """
        Returns the UTC second-of-day [0..86399].
        """
        return (self.value // _MILLISECONDS_PER_SECOND) % _SECONDS_PER_DAY

    @staticmethod
    def from_datetime(dt: datetime) -> EpochMs:
        """
        Creates EpochMs from a timezone-aware datetime.

        Requirements:
        - dt must be tz-aware
        - dt must be in UTC
        """
        if not isinstance(dt, datetime):
            raise InvariantViolation("dt must be a datetime")

        if dt.tzinfo is None:
            raise InvariantViolation("datetime must be timezone-aware")

        if dt.tzinfo != UTC:
            raise InvariantViolation("datetime must be in UTC")

        delta = dt - _EPOCH_UTC
        return EpochMs(int(delta.total_seconds() * _MILLISECONDS_PER_SECOND))
