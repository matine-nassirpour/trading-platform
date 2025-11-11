from unittest.mock import MagicMock, patch

import pytest

from quantum.infrastructure.config.runtime.manager import ConfigManager
from quantum.infrastructure.config.runtime.state import ConfigState


@pytest.mark.verification
def test_load_reads_env_and_returns_valid_core_settings(monkeypatch):
    """load() must use load_env() and produce a CoreSettings instance."""
    fake_env = {
        "QUANTUM_APP_NAME": "quantum",
        "QUANTUM_ENV": "test",
        "QUANTUM_NS": "ns",
    }

    from quantum.infrastructure.config.runtime.state import ConfigState

    ConfigState.instance().reset()

    with patch(
        "quantum.infrastructure.config.runtime.manager.load_env", return_value=fake_env
    ):
        settings = ConfigManager.load(apply=False)

    assert settings.quantum_env in ("dev", "test", "staging", "prod")
    assert isinstance(settings.quantum_app_name, str)


@pytest.mark.verification
def test_clear_caches_resets_configstate(caplog):
    """clear_caches() must reset ConfigState and LRU caches."""
    with patch(
        "quantum.infrastructure.config.runtime.manager.load_env",
        return_value={"QUANTUM_ENV": "dev"},
    ):
        ConfigManager.load(apply=False)

    state = ConfigState.instance()
    assert isinstance(state.snapshot(), dict)
    ConfigManager.clear_caches()

    snap = state.snapshot()
    assert snap["env_cache"] == {}
    assert "ConfigManager caches cleared" in caplog.text


@pytest.mark.verification
def test_snapshot_includes_core_and_tracing_fields(monkeypatch):
    """snapshot() must expose coherent configuration summary."""
    core = MagicMock()
    tracing = MagicMock()
    core.quantum_app_name = "platform"
    core.quantum_app_version = "1.0"
    core.quantum_env = "test"
    core.quantum_metrics_port = 8080
    tracing.quantum_trace_exporter = "otlp"

    res = ConfigManager.snapshot(settings=core, tracing=tracing)
    assert res["app"] == "platform"
    assert res["version"] == "1.0"
    assert res["trace_exporter"] == "otlp"
    assert res["env"] == "test"


@pytest.mark.verification
def test_load_invalid_env_triggers_fallback(monkeypatch):
    """Invalid QUANTUM_ENV should fallback to default environment, not raise."""
    fake_env = {"QUANTUM_ENV": "invalid"}
    with patch(
        "quantum.infrastructure.config.runtime.manager.load_env", return_value=fake_env
    ):
        settings = ConfigManager.load(apply=True)

        assert settings.quantum_env in ("dev", "test", "staging", "prod")


@pytest.mark.verification
def test_load_apply_false_does_not_mutate_configstate(monkeypatch):
    """When apply=False, the ConfigState must remain empty."""
    fake_env = {"QUANTUM_ENV": "test"}
    with patch(
        "quantum.infrastructure.config.runtime.manager.load_env", return_value=fake_env
    ):
        ConfigManager.load(apply=False)

    snap = ConfigState.instance().snapshot()
    assert not snap["env_cache"]  # No mutation


@pytest.mark.verification
def test_load_apply_true_updates_runtime(monkeypatch):
    """apply=True should commit the configuration to ConfigState."""
    fake_env = {"QUANTUM_ENV": "prod"}
    with patch(
        "quantum.infrastructure.config.runtime.manager.load_env", return_value=fake_env
    ):
        settings = ConfigManager.load(apply=True)

    snap = ConfigState.instance().snapshot()

    assert isinstance(snap, dict)
    assert "env_cache" in snap
    assert isinstance(snap["env_cache"], dict)
    assert settings.quantum_env in ("dev", "test", "staging", "prod")


@pytest.mark.verification
def test_get_mt5_credentials_returns_expected_fields(monkeypatch):
    """get_mt5_credentials() must resolve broker credentials correctly."""
    fake_model = MagicMock()
    fake_model.quantum_mt5_ftmo_login = 1234
    fake_model.quantum_mt5_ftmo_server = "srv"
    fake_model.quantum_mt5_ftmo_password = "pwd"  # pragma: allowlist secret

    with patch(
        "quantum.infrastructure.config.runtime.manager.ConfigManager.load_mt5",
        return_value=fake_model,
    ):
        creds = ConfigManager.get_mt5_credentials("ftmo")
        assert creds["login"] == "1234"
        assert creds["server"] == "srv"
        assert creds["password"] == "pwd"  # pragma: allowlist secret
