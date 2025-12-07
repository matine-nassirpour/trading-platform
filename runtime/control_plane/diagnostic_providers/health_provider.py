from runtime.control_plane.diagnostic_providers.time_provider_dependency import (
    TimeProviderDependency,
)


class HealthProvider:
    """
    Responsibility: Produce minimal liveness snapshot.
    No HTTP, no JSON.
    """

    @staticmethod
    def get_health() -> dict:
        time_provider = TimeProviderDependency.get()
        return {
            "status": "ok",
            "timestamp_utc": time_provider.now_utc().isoformat(),
        }
