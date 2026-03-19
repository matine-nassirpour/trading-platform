from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from quantum.domain.shared_kernel.ddd.value_objects.value_object import ValueObject
from quantum.domain.shared_kernel.foundation.errors.invariants import InvariantViolation

_SECONDS_PER_DAY = 86_400
_MILLISECONDS_PER_SECOND = 1_000
_MILLISECONDS_PER_DAY = _SECONDS_PER_DAY * _MILLISECONDS_PER_SECOND

_EPOCH_UTC = datetime(1970, 1, 1, tzinfo=UTC)


@dataclass(frozen=True, slots=True)
class EpochMs(ValueObject):
    """
    Canonical epoch timestamp in milliseconds since Unix epoch (UTC).

    HARD GUARANTEES:
    - integer only
    - UTC only
    - no floating point arithmetic
    - deterministic conversions
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
        Converts to a timezone-aware UTC datetime.

        No floating-point arithmetic is used.
        """
        seconds, millis = divmod(self.value, _MILLISECONDS_PER_SECOND)

        return _EPOCH_UTC + timedelta(
            seconds=seconds,
            milliseconds=millis,
        )

    def to_utc_second_of_day(self) -> int:
        """
        Returns second-of-day [0..86399].
        """
        return (self.value // _MILLISECONDS_PER_SECOND) % _SECONDS_PER_DAY

    def to_utc_minute_of_day(self) -> int:
        """
        Returns minute-of-day [0..1439].
        """
        return self.to_utc_second_of_day() // 60

    @staticmethod
    def from_datetime(dt: datetime) -> EpochMs:
        """
        Creates EpochMs from a UTC datetime.

        STRICT:
        - tz-aware only
        - must be UTC
        - no floating-point conversion
        """

        if not isinstance(dt, datetime):
            raise InvariantViolation("dt must be a datetime")

        if dt.tzinfo is None:
            raise InvariantViolation("datetime must be timezone-aware")

        if dt.tzinfo != UTC:
            raise InvariantViolation("datetime must be in UTC")

        delta = dt - _EPOCH_UTC

        total_ms = (
            delta.days * _MILLISECONDS_PER_DAY
            + delta.seconds * _MILLISECONDS_PER_SECOND
            + delta.microseconds // 1000
        )

        return EpochMs(total_ms)
