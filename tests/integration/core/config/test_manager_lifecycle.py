import os
import threading
from pathlib import Path

import pytest
from pydantic import ValidationError

from quantum.core.config.models.core import CoreSettings
from quantum.core.config.models.logging import LoggingSettings
from quantum.core.config.models.mt5 import MT5Settings
from quantum.core.config.models.tracing import TracingSettings
from quantum.core.config.runtime.manager import ConfigManager
from quantum.core.config.runtime.state import ConfigState


@pytest.mark.integration
def test_core_load_creates_valid_model(tmp_path: Path, iso_env):
    """
    Load a minimal .env file and ensure ConfigManager.load() returns a valid CoreSettings.
    """
    (tmp_path / ".env").write_text(
        "\n".join(
            [
                "QUANTUM_APP_NAME=test_app",
                "QUANTUM_ENV=staging",
                "QUANTUM_METRICS_PORT=8080",
            ]
        ),
        encoding="utf-8",
    )

    settings = ConfigManager.load(root=tmp_path, apply=True)
    assert isinstance(settings, CoreSettings)
    assert settings.quantum_app_name == "test_app"
    assert settings.quantum_env == "staging"
    assert settings.quantum_metrics_port == 8080

    state = ConfigState.instance()
    snap = state.snapshot()
    assert snap["loaded_pid"] == os.getpid()
    assert "QUANTUM_APP_NAME" in snap["env_cache"]


@pytest.mark.integration
def test_secondary_loaders_return_valid_models(tmp_workspace):
    core = ConfigManager.load(apply=False)
    log = ConfigManager.load_logging()
    trace = ConfigManager.load_tracing()
    mt5 = ConfigManager.load_mt5()

    assert isinstance(core, CoreSettings)
    assert isinstance(log, LoggingSettings)
    assert isinstance(trace, TracingSettings)
    assert isinstance(mt5, MT5Settings)

    exception_types: tuple[type[BaseException], ...] = (TypeError, ValidationError)

    for m in (log, trace, mt5):
        with pytest.raises(exception_types):
            m.streamlit_log_glob = "x"

    core.quantum_app_name = "mutable_test"
    assert core.quantum_app_name == "mutable_test"


@pytest.mark.integration
def test_clear_caches_resets_all_state(tmp_workspace):
    """
    Ensure ConfigManager.clear_caches() resets all LRU caches and ConfigState.
    """
    ConfigManager.load(apply=False)
    ConfigManager.load_logging()
    ConfigManager.load_tracing()
    ConfigManager.load_mt5()

    state = ConfigState.instance()
    assert state.has_valid_cache()

    ConfigManager.clear_caches()
    assert not state.has_valid_cache()

    new = ConfigManager.load(apply=False)
    assert isinstance(new, CoreSettings)
    assert state.has_valid_cache()


@pytest.mark.integration
def test_snapshot_returns_minimal_consistent_view(tmp_workspace):
    """
    ConfigManager.snapshot() should produce a minimal coherent dict view.
    """
    s = ConfigManager.load(apply=False)
    t = ConfigManager.load_tracing()

    snap = ConfigManager.snapshot(s, t)
    expected_keys = {"app", "version", "env", "trace_exporter", "metrics_port"}

    assert set(snap.keys()) == expected_keys
    assert snap["app"] == s.quantum_app_name
    assert snap["env"] == s.quantum_env
    assert snap["trace_exporter"] == t.quantum_trace_exporter


@pytest.mark.integration
def test_environment_isolation_between_loads(tmp_workspace, iso_env):
    """
    Changing os.environ after the first load should not mutate cached models.
    """
    s1 = ConfigManager.load(apply=False)
    assert s1.quantum_env == "test"

    os.environ["QUANTUM_ENV"] = "prod"
    s2 = ConfigManager.load(apply=False)

    assert s2 is s1
    assert s2.quantum_env == "test"

    ConfigManager.clear_caches()
    s3 = ConfigManager.load(apply=False)
    assert s3.quantum_env in ("test", "prod")


@pytest.mark.integration
def test_get_mt5_credentials_handles_partial_values(tmp_workspace):
    """
    get_mt5_credentials() must return safe string values even if env vars are missing.
    """
    creds = ConfigManager.get_mt5_credentials("ftmo")
    assert set(creds.keys()) == {"login", "server", "password"}
    assert all(isinstance(v, str) for v in creds.values())


@pytest.mark.integration
def test_thread_safe_access_to_loaders(tmp_workspace):
    """
    Multiple threads calling ConfigManager.load_logging() concurrently
    must receive the same cached instance, without race conditions.
    """
    results: list[LoggingSettings] = []

    def worker():
        results.append(ConfigManager.load_logging())

    threads = [threading.Thread(target=worker) for _ in range(10)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert all(isinstance(r, LoggingSettings) for r in results)
    assert len({id(r) for r in results}) == 1
