from datetime import date, datetime
from typing import Protocol


class TimeProviderPort(Protocol):
    """
    Abstract time provider for deterministic UTC time access.

    This protocol defines the interface through which the Application layer
    retrieves the current time, independently of the underlying implementation
    (system clock, market feed, simulation clock, etc.).
    """

    def now_utc(self) -> datetime:
        """Return the current UTC datetime."""
        ...

    def today_utc(self) -> date:
        """Return the current UTC date."""
        ...
