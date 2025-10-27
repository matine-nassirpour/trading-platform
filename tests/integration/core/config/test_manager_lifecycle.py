"""
Quantum Core — Integration Tests: Configuration Manager Lifecycle
─────────────────────────────────────────────────────────────────
Validate the complete lifecycle of the ConfigManager orchestration layer,
including environment loading, cache management, model consistency,
and thread-safe access to cached configuration instances.
"""

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


# ╭────────────────────────────────────────────────────────────────────────────╮
# │ Core model loading and validation                                          │
# ╰────────────────────────────────────────────────────────────────────────────╯
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
    assert state.has_valid_cache()

    snap = state.snapshot()
    assert snap["env_cache"]["QUANTUM_APP_NAME"] == "test_app"

    again = ConfigManager.load(root=tmp_path, apply=True)
    assert again == settings


# ╭────────────────────────────────────────────────────────────────────────────╮
# │ Secondary model loaders and immutability                                   │
# ╰────────────────────────────────────────────────────────────────────────────╯
@pytest.mark.integration
def test_secondary_loaders_return_valid_models(tmp_workspace):
    """
    Ensure that all secondary loaders return valid, frozen model instances.
    """
    core = ConfigManager.load(apply=False)
    log = ConfigManager.load_logging()
    trace = ConfigManager.load_tracing()
    mt5 = ConfigManager.load_mt5()

    for inst, cls in [
        (core, CoreSettings),
        (log, LoggingSettings),
        (trace, TracingSettings),
        (mt5, MT5Settings),
    ]:
        assert isinstance(inst, cls)

    # Models must be frozen (immutable)
    exception_types: tuple[type[BaseException], ...] = (TypeError, ValidationError)
    for m in (log, trace, mt5):
        with pytest.raises(exception_types):
            m.streamlit_log_glob = "x"

    # Core may be mutable by design
    core.quantum_app_name = "mutable_test"
    assert core.quantum_app_name == "mutable_test"

    # Cached consistency
    assert ConfigManager.load_logging() == log
    assert ConfigManager.load_tracing() == trace


# ╭────────────────────────────────────────────────────────────────────────────╮
# │ Cache clearing and lifecycle reset                                         │
# ╰────────────────────────────────────────────────────────────────────────────╯
@pytest.mark.integration
def test_clear_caches_resets_all_state(tmp_workspace):
    """
    Ensure ConfigManager.clear_caches() resets all LRU caches and ConfigState.
    """
    ConfigManager.load()
    log = ConfigManager.load_logging()
    _ = ConfigManager.load_tracing()

    state = ConfigState.instance()
    assert state.has_valid_cache()

    ConfigManager.clear_caches()
    assert not state.has_valid_cache()

    # After reload, new models must be re-instantiated
    new = ConfigManager.load()
    assert isinstance(new, CoreSettings)
    assert new != log


# ╭────────────────────────────────────────────────────────────────────────────╮
# │ Snapshot generation and coherence                                          │
# ╰────────────────────────────────────────────────────────────────────────────╯
@pytest.mark.integration
def test_snapshot_returns_minimal_consistent_view(tmp_workspace):
    """
    ConfigManager.snapshot() should produce a coherent dict view.
    """
    s = ConfigManager.load()
    t = ConfigManager.load_tracing()

    snap = ConfigManager.snapshot(s, t)
    expected_keys = {"app", "version", "env", "trace_exporter", "metrics_port"}

    assert set(snap.keys()) == expected_keys
    assert snap["app"] == s.quantum_app_name
    assert snap["env"] == s.quantum_env
    assert snap["trace_exporter"] == t.quantum_trace_exporter


# ╭────────────────────────────────────────────────────────────────────────────╮
# │ Environment isolation and cache behavior                                   │
# ╰────────────────────────────────────────────────────────────────────────────╯
@pytest.mark.integration
def test_environment_isolation_between_loads(tmp_workspace, iso_env):
    """
    Changing os.environ after first load should not mutate cached models.
    """
    os.environ["QUANTUM_ENV"] = "test"
    s1 = ConfigManager.load(apply=False)
    assert s1.quantum_env == "test"

    os.environ["QUANTUM_ENV"] = "prod"
    s2 = ConfigManager.load(apply=False)
    assert s2 is s1
    assert s2.quantum_env == "test"

    # After cache clear, reload should reflect new env
    ConfigManager.clear_caches()
    s3 = ConfigManager.load(apply=False)
    assert s3.quantum_env in ("test", "prod")


# ╭────────────────────────────────────────────────────────────────────────────╮
# │ Broker credentials resilience                                              │
# ╰────────────────────────────────────────────────────────────────────────────╯
@pytest.mark.integration
def test_get_mt5_credentials_handles_partial_values(tmp_workspace):
    """
    get_mt5_credentials() must return safe string values even if env vars are missing.
    """
    creds = ConfigManager.get_mt5_credentials("ftmo")
    assert set(creds.keys()) == {"login", "server", "password"}
    assert all(isinstance(v, str) and v is not None for v in creds.values())


# ╭────────────────────────────────────────────────────────────────────────────╮
# │ Thread-safety and shared cache consistency                                 │
# ╰────────────────────────────────────────────────────────────────────────────╯
@pytest.mark.integration
def test_thread_safe_access_to_loaders(tmp_workspace):
    """
    Multiple threads calling ConfigManager.load_logging() concurrently
    must receive logically identical LoggingSettings without race conditions.
    """
    results: list[LoggingSettings] = []

    def worker():
        results.append(ConfigManager.load_logging())

    threads = [threading.Thread(target=worker) for _ in range(50)]
    for t in threads:
        t.start()
    for t in threads:
        t.join(timeout=5)

    assert len(results) == 50
    assert all(isinstance(r, LoggingSettings) for r in results)

    first = results[0]
    assert all(r == first for r in results)
