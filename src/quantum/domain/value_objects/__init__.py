"""
Canonical, immutable, and validated data structures representing atomic
concepts in the trading domain.

Guarantees:
- Full immutability (hashable, equality by value)
- Validation and normalization performed at model validation time
- Strict encapsulation: cannot be mutated or subclassed improperly
- Clean representation and diagnostics
"""

from __future__ import annotations

import re
import uuid

from datetime import datetime, timezone
from typing import Any, ClassVar

from pydantic import BaseModel, ConfigDict, Field, field_validator


# ╭────────────────────────────────────────────────────────────────────────────╮
# │ Base class                                                                 │
# ╰────────────────────────────────────────────────────────────────────────────╯
class ValueObject(BaseModel):
    """
    Canonical base for all Value Objects in the system.

    - Immutable and hashable
    - Equality by value
    - No runtime mutation allowed
    - Strict schema: extra fields forbidden
    """

    model_config = ConfigDict(
        frozen=True,
        extra="forbid",
        validate_assignment=False,
        arbitrary_types_allowed=False,
        str_min_length=1,
    )

    # ─── Equality & Hash semantics
    def __eq__(self, other: Any) -> bool:
        if self.__class__ is not other.__class__:
            return False
        return self.model_dump() == other.model_dump()

    def __hash__(self) -> int:
        # Hash by sorted tuple of fields to ensure deterministic hashing
        return hash(tuple(sorted(self.model_dump().items())))

    # ─── String representations
    def __str__(self) -> str:  # human-readable
        return str(self.value)

    def __repr__(self) -> str:
        cls = self.__class__.__name__
        payload = ", ".join(f"{k}={v!r}" for k, v in self.model_dump().items())
        return f"{cls}({payload})"


# ╭────────────────────────────────────────────────────────────────────────────╮
# │ Identifiers (UUID-based or numeric)                                        │
# ╰────────────────────────────────────────────────────────────────────────────╯
class IntentId(ValueObject):
    value: uuid.UUID = Field(..., description="Unique identifier for an order intent")

    @classmethod
    def new(cls) -> IntentId:
        return cls(value=uuid.uuid4())

    @field_validator("value", mode="before")
    @classmethod
    def _coerce_uuid(cls, v):
        if isinstance(v, uuid.UUID):
            return v
        return uuid.UUID(str(v))


class OrderId(ValueObject):
    value: int = Field(..., ge=1, description="Broker order identifier (positive int)")


class DealId(ValueObject):
    value: int = Field(..., ge=1, description="Broker deal identifier (positive int)")


class PositionId(ValueObject):
    value: int = Field(
        ..., ge=1, description="Broker position identifier (positive int)"
    )


# ╭────────────────────────────────────────────────────────────────────────────╮
# │ Temporal primitives                                                        │
# ╰────────────────────────────────────────────────────────────────────────────╯
class EpochMs(ValueObject):
    """
    UNIX epoch timestamp in milliseconds.
    Immutable and validated; guarantees non-negative integer.
    """

    value: int

    @classmethod
    def now(cls) -> EpochMs:
        """Returns the current UTC epoch time (ms)."""
        ms = int(datetime.now(tz=timezone.utc).timestamp() * 1_000)
        return cls(value=ms)

    @classmethod
    def from_datetime(cls, dt: datetime) -> EpochMs:
        """Converts a timezone-aware UTC datetime to EpochMs."""
        if dt.tzinfo is None:
            raise ValueError("datetime must be timezone-aware (UTC)")
        return cls(value=int(dt.timestamp() * 1_000))

    @classmethod
    def from_seconds(cls, seconds: float) -> EpochMs:
        """Converts a UNIX timestamp (float seconds) to EpochMs."""
        return cls(value=int(seconds * 1_000))

    @field_validator("value")
    @classmethod
    def _validate_positive(cls, v: int) -> int:
        if v < 0:
            raise ValueError("EpochMs must be non-negative")
        return v

    def to_seconds(self) -> float:
        """Returns the UNIX timestamp in seconds (float)."""
        return self.value / 1_000

    def to_datetime(self) -> datetime:
        """Returns a UTC datetime equivalent of this epoch."""
        return datetime.fromtimestamp(self.to_seconds(), tz=timezone.utc)


# ╭────────────────────────────────────────────────────────────────────────────╮
# │ Symbol                                                                     │
# ╰────────────────────────────────────────────────────────────────────────────╯
class Symbol(ValueObject):
    """
    Trading symbol (currency pair, instrument identifier, etc.).

    Invariants:
    - Uppercased (e.g., EURUSD, XAUUSD)
    - Matches the canonical pattern: uppercase alphanumerics only
    - Immutable and validated at construction
    """

    value: str

    _PATTERN: ClassVar[re.Pattern[str]] = re.compile(r"^[A-Z0-9._\-]{3,20}$")

    @field_validator("value")
    @classmethod
    def _normalize_and_validate(cls, v: str) -> str:
        if not v or not isinstance(v, str):
            raise ValueError("Symbol value must be a non-empty string.")
        val = v.strip().upper()
        if not cls._PATTERN.match(val):
            raise ValueError(
                f"Invalid symbol format '{v}': must match pattern {cls._PATTERN.pattern}"
            )
        return val


# ╭────────────────────────────────────────────────────────────────────────────╮
# │ Version metadata (for registry stability)                                  │
# ╰────────────────────────────────────────────────────────────────────────────╯
VALUE_OBJECTS_VERSION = 2
