from datetime import UTC, datetime


class HealthAdapter:
    """
    Responsibility: Produce minimal liveness snapshot.
    No HTTP, no JSON.
    """

    @staticmethod
    def get_health() -> dict:
        return {
            "status": "ok",
            "timestamp_utc": datetime.now(UTC).isoformat(),
        }
