from __future__ import annotations

import re
import uuid
from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, Field, field_validator

# ──────────────────────────────────────────────────────────────────────────────
# Base class
# ──────────────────────────────────────────────────────────────────────────────


class ValueObject(BaseModel):
    """
    Immutable and comparable base for lightweight domain primitives.

    Design goals:
    - Immutability and equality by *value* (DDD semantics)
    - Human-readable __str__ / __repr__
    - Isolation from Pydantic internal equality behavior
    """

    model_config = dict(frozen=True, extra="forbid")

    # ─── Equality & Hash semantics
    def __eq__(self, other: Any) -> bool:
        """Equality by underlying value and exact class type."""
        if isinstance(other, self.__class__):
            return self.value == other.value
        return False

    def __hash__(self) -> int:
        """Hash based on class name and underlying value."""
        return hash((self.__class__.__name__, self.value))

    # ─── String representations
    def __str__(self) -> str:  # human-readable
        return str(self.value)

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.value!r})"


# ──────────────────────────────────────────────────────────────────────────────
# Identifiers (UUID-based or numeric)
# ──────────────────────────────────────────────────────────────────────────────


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


# ──────────────────────────────────────────────────────────────────────────────
# Temporal primitives
# ──────────────────────────────────────────────────────────────────────────────


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


# ──────────────────────────────────────────────────────────────────────────────
# Symbol
# ──────────────────────────────────────────────────────────────────────────────

_SYMBOL_PATTERN = re.compile(r"^[A-Z]{3,6}$")  # e.g. EURUSD, XAUUSD


class Symbol(ValueObject):
    """
    Canonical trading symbol.

    Enforces uppercase, strips spaces and broker-specific suffixes.
    Compatible with MT5, FIX, and internal canonical representation.
    """

    value: str = Field(..., description="Normalized trading symbol (e.g. EURUSD)")

    @field_validator("value", mode="before")
    @classmethod
    def _normalize(cls, v: str) -> str:
        s = str(v).strip().upper()
        s = re.sub(r"\.[A-Z0-9]+$", "", s)  # remove broker suffixes like ".r"
        if not _SYMBOL_PATTERN.match(s):
            raise ValueError(f"Invalid symbol format: {v!r}")
        return s


# ──────────────────────────────────────────────────────────────────────────────
# Version metadata (for registry stability)
# ──────────────────────────────────────────────────────────────────────────────

VALUE_OBJECTS_VERSION = 2
