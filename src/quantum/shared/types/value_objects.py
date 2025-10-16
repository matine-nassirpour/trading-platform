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

_SYMBOL_PATTERN = re.compile(r"^[A-Z0-9._\-]{3,20}$")


class Symbol(ValueObject):
    """
    Canonical trading symbol.

    Designed to support Forex, Indices, Commodities,
    Equities, and Crypto, while enforcing naming consistency and validation.
    """

    value: str

    def __post_init__(self) -> None:
        val = self.value.strip().upper()

        if not _SYMBOL_PATTERN.match(val):
            raise ValueError(
                f"Invalid trading symbol '{self.value}'. "
                "Allowed pattern: uppercase letters, digits, '.', '_', '-'; length 3–20."
            )

        # Set normalized uppercase value
        object.__setattr__(self, "value", val)

    # ─── Equality & hashing
    def __eq__(self, other: object) -> bool:
        if isinstance(other, Symbol):
            return self.value == other.value
        if isinstance(other, str):
            return self.value == other.strip().upper()
        return False

    def __hash__(self) -> int:
        return hash(self.value)

    # ─── Representation
    def __str__(self) -> str:
        return self.value

    def __repr__(self) -> str:
        return f"Symbol('{self.value}')"

    # ─── Utilities
    def is_forex(self) -> bool:
        """Heuristic: symbol has 6 letters and ends with USD, EUR, JPY, etc."""
        return len(self.value) == 6 and self.value[-3:] in {
            "USD",
            "EUR",
            "JPY",
            "GBP",
            "CHF",
            "CAD",
            "AUD",
            "NZD",
        }

    def is_index(self) -> bool:
        """Heuristic for indices (starts with US, DE, JP, HK, etc.)."""
        return bool(re.match(r"^(US|DE|JP|FR|HK|UK|SP)\d+", self.value))

    def is_crypto(self) -> bool:
        """Heuristic for crypto pairs."""
        return self.value.startswith(("BTC", "ETH", "XRP", "SOL", "ADA", "DOGE"))


# ──────────────────────────────────────────────────────────────────────────────
# Version metadata (for registry stability)
# ──────────────────────────────────────────────────────────────────────────────

VALUE_OBJECTS_VERSION = 2
