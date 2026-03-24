from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Final, final

from quantum.domain.shared_kernel.foundation.errors.invariants import InvariantViolation
from quantum.domain.shared_kernel.modeling.value_objects.value_object import ValueObject

_SECONDS_PER_DAY: Final[int] = 86_400
_MILLISECONDS_PER_SECOND: Final[int] = 1_000
_MICROSECONDS_PER_MILLISECOND: Final[int] = 1_000
_MILLISECONDS_PER_DAY: Final[int] = _SECONDS_PER_DAY * _MILLISECONDS_PER_SECOND

_EPOCH_UTC: Final[datetime] = datetime(1970, 1, 1, tzinfo=UTC)


def _require_utc_datetime(dt: datetime) -> None:
    """
    Enforces the canonical temporal input contract for EpochMs conversion.

    HARD GUARANTEES:
    - dt must be a datetime
    - dt must be timezone-aware
    - dt must be explicitly UTC
    - dt must be aligned to the millisecond
    """
    if not isinstance(dt, datetime):
        raise InvariantViolation("dt must be a datetime")

    if dt.tzinfo is None:
        raise InvariantViolation("datetime must be timezone-aware")

    if dt.tzinfo != UTC:
        raise InvariantViolation("datetime must be expressed in UTC using datetime.UTC")

    if dt.microsecond % _MICROSECONDS_PER_MILLISECOND != 0:
        raise InvariantViolation(
            "datetime must be aligned to the millisecond; "
            "sub-millisecond precision is forbidden"
        )


@final
@dataclass(frozen=True, slots=True)
class EpochMs(ValueObject):
    """
    Canonical UTC timestamp represented as milliseconds since Unix epoch.

    HARD GUARANTEES:
    - integer only
    - non-negative only
    - UTC only
    - millisecond precision only
    - no floating-point arithmetic
    - no silent quantization or truncation
    - deterministic conversions
    """

    value: int

    def _validate_semantics(self) -> None:
        if not isinstance(self.value, int):
            raise InvariantViolation("EpochMs must be an integer")

        if self.value < 0:
            raise InvariantViolation("EpochMs must be non-negative")

    # --- Conversions ----------------------------------------------------------

    def to_datetime(self) -> datetime:
        """
        Converts this timestamp to a timezone-aware UTC datetime.

        GUARANTEES:
        - exact millisecond-preserving conversion
        - no floating-point arithmetic
        - returned datetime is always timezone-aware UTC
        """
        seconds, millis = divmod(self.value, _MILLISECONDS_PER_SECOND)

        return _EPOCH_UTC + timedelta(
            seconds=seconds,
            milliseconds=millis,
        )

    def to_utc_second_of_day(self) -> int:
        """
        Returns the UTC second-of-day in [0..86399].
        """
        return (self.value // _MILLISECONDS_PER_SECOND) % _SECONDS_PER_DAY

    def to_utc_minute_of_day(self) -> int:
        """
        Returns the UTC minute-of-day in [0..1439].
        """
        return self.to_utc_second_of_day() // 60

    def to_utc_millisecond_of_day(self) -> int:
        """
        Returns the UTC millisecond-of-day in [0..86_399_999].
        """
        return self.value % _MILLISECONDS_PER_DAY

    @staticmethod
    def from_datetime(dt: datetime) -> EpochMs:
        """
        Creates an EpochMs from a timezone-aware UTC datetime.

        STRICT CONTRACT:
        - dt must be a datetime
        - dt must be timezone-aware
        - dt must use datetime.UTC
        - dt must be aligned to the millisecond
        - no floating-point conversion is allowed
        - no silent precision loss is allowed

        IMPORTANT:
        A datetime with sub-millisecond precision is rejected, not rounded and
        not truncated.
        """
        _require_utc_datetime(dt)

        delta = dt - _EPOCH_UTC

        total_ms = (
            delta.days * _MILLISECONDS_PER_DAY
            + delta.seconds * _MILLISECONDS_PER_SECOND
            + (delta.microseconds // _MICROSECONDS_PER_MILLISECOND)
        )

        return EpochMs(total_ms)

    @staticmethod
    def from_components(
        *,
        year: int,
        month: int,
        day: int,
        hour: int = 0,
        minute: int = 0,
        second: int = 0,
        millisecond: int = 0,
    ) -> EpochMs:
        """
        Creates an EpochMs from explicit UTC calendar components.

        This constructor avoids accidental sub-millisecond input entirely.
        """
        if not isinstance(millisecond, int):
            raise InvariantViolation("millisecond must be an integer")

        if millisecond < 0 or millisecond >= _MILLISECONDS_PER_SECOND:
            raise InvariantViolation("millisecond must be in range [0..999]")

        dt = datetime(
            year=year,
            month=month,
            day=day,
            hour=hour,
            minute=minute,
            second=second,
            microsecond=millisecond * _MICROSECONDS_PER_MILLISECOND,
            tzinfo=UTC,
        )

        return EpochMs.from_datetime(dt)

    def __str__(self) -> str:
        return str(self.value)
