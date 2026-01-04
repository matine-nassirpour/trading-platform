from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from quantum.domain.shared_kernel.errors.invariants import InvariantViolation
from quantum.domain.shared_kernel.primitives.value_object import ValueObject

_EPOCH_UTC = datetime(1970, 1, 1, tzinfo=UTC)


@dataclass(frozen=True)
class EpochMs(ValueObject):
    """
    Milliseconds since Unix epoch (UTC).

    Design guarantees:
    - Integer-only representation
    - No floating-point arithmetic
    - Deterministic and platform-independent
    - Suitable for safety / certifiable contexts
    """

    value: int

    # --- Invariants -----------------------------------------------------------

    def _validate(self) -> None:
        if not isinstance(self.value, int):
            raise InvariantViolation("EpochMs must be an integer")

        if self.value < 0:
            raise InvariantViolation("EpochMs must be non-negative")

    # --- Conversions ----------------------------------------------------------

    def to_datetime(self) -> datetime:
        """
        Converts EpochMs to a timezone-aware UTC datetime.

        Implementation:
        - integer seconds + integer milliseconds
        - no float conversion
        """
        seconds, milliseconds = divmod(self.value, 1000)

        return _EPOCH_UTC + timedelta(
            seconds=seconds,
            milliseconds=milliseconds,
        )

    @classmethod
    def from_datetime(cls, dt: datetime) -> EpochMs:
        """
        Converts a timezone-aware datetime to EpochMs.

        Requirements:
        - dt MUST be timezone-aware
        - dt is normalized to UTC
        - conversion uses integer arithmetic only
        """
        if not isinstance(dt, datetime):
            raise InvariantViolation("dt must be a datetime instance")

        if dt.tzinfo is None:
            raise InvariantViolation("Datetime must be timezone-aware")

        dt_utc = dt.astimezone(UTC)

        delta: timedelta = dt_utc - _EPOCH_UTC

        # Total milliseconds using integer arithmetic only
        total_ms = (
            delta.days * 86_400_000
            + delta.seconds * 1_000
            + delta.microseconds // 1_000
        )

        return cls(total_ms)
