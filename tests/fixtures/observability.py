import pytest

from quantum.infrastructure.config.models.logging import LoggingSettings
from tests.support.logging_utils import close_all_handlers


@pytest.fixture(scope="function")
def clean_registry(monkeypatch):
    """
    Isolate the Prometheus registry per test (Counter/Gauge/Histogram).

    Avoids metric name collisions and shared state across tests by providing
    a fresh CollectorRegistry and monkeypatching common access points.
    """
    try:
        import prometheus_client

        from prometheus_client import CollectorRegistry
        from prometheus_client import core as pc_core
    except Exception:
        # Prometheus not present / not used by the test
        yield
        return

    reg = CollectorRegistry()

    # Monkeypatch the most common access points
    monkeypatch.setattr(prometheus_client, "REGISTRY", reg, raising=False)
    monkeypatch.setattr(pc_core, "REGISTRY", reg, raising=False)

    yield


@pytest.fixture(scope="function")
def make_observability(tmp_workspace):
    """Factory fixture to build ObservabilitySettings with test-safe defaults."""

    def _factory(**overrides) -> LoggingSettings:
        defaults = dict(
            quantum_log_dir=str(tmp_workspace["logs"]),
            quantum_audit_dir=str(tmp_workspace["audit"]),
            quantum_log_fsync=False,
            quantum_log_max_bytes=0,
            quantum_log_warn_bytes=0,
        )
        return LoggingSettings(**{**defaults, **overrides})

    return _factory


@pytest.fixture(scope="function")
def obs_session(tmp_workspace):
    """
    Open a full observability session in a controlled context and guarantee
    a clean closure (freeing FDs/handlers).
    """
    from quantum.infrastructure.observability.bootstrap.init_manager import (
        observability_session,
    )

    with observability_session(
        force=True,
    ):
        yield

    # Safety (observability_session already performs the shutdown)
    close_all_handlers()
