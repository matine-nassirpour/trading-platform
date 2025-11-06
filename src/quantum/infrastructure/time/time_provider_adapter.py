from datetime import UTC, date, datetime

from quantum.application.ports.outbound.time_provider_port import TimeProviderPort


class SystemTimeProviderAdapter(TimeProviderPort):
    """
    Provides real UTC time based on the system clock.

    This adapter implements the TimeProviderPort interface, allowing
    the Application layer to retrieve current time information without
    directly accessing system libraries.
    """

    def now_utc(self) -> datetime:
        """Return the current UTC datetime."""
        return datetime.now(UTC)

    def today_utc(self) -> date:
        """Return the current UTC date."""
        return datetime.now(UTC).date()

    def __repr__(self) -> str:
        return f"<SystemTimeProvider now={self.now_utc().isoformat()}>"
