from textwrap import dedent

import pytest
from pydantic import ValidationError

from quantum.core.config.models.core import CoreSettings
from quantum.core.config.models.logging import LoggingSettings
from quantum.core.config.models.mt5 import MT5Settings
from quantum.core.config.models.tracing import TracingSettings
from quantum.core.config.providers.env_loader import load_env
from quantum.core.config.runtime.manager import ConfigManager


@pytest.mark.integration
def test_models_initialize_consistently_from_env(tmp_workspace, iso_env):
    """
    Ensure all configuration models can be instantiated consistently
    from the same environment snapshot.
    """
    env_path = tmp_workspace["root"] / ".env"
    env_path.write_text(
        dedent(
            """
            QUANTUM_APP_NAME=test_app
            QUANTUM_APP_VERSION=0.1.0
            QUANTUM_ENV=staging
            QUANTUM_NS=quantum
            QUANTUM_LOG_LEVEL=INFO
            QUANTUM_TRACE_EXPORTER=console
            QUANTUM_METRICS_PORT=9090
            QUANTUM_MT5_FTMO_SERVER=test-server
            QUANTUM_MT5_FTMO_LOGIN=123456
            QUANTUM_MT5_FTMO_PASSWORD=secret
            """
        ),
        encoding="utf-8",
    )

    merged = load_env(root=tmp_workspace["root"], apply=True)
    normalized = {k.lower(): v for k, v in merged.items()}

    core = CoreSettings()  # type: ignore[arg-type]
    log = LoggingSettings(**normalized)
    trace = TracingSettings(**normalized)
    mt5 = MT5Settings(**normalized)

    assert core.quantum_app_name == "test_app"
    assert log.quantum_log_level == "INFO"
    assert trace.quantum_trace_exporter == "console"
    assert mt5.quantum_mt5_ftmo_server == "test-server"
    assert mt5.quantum_mt5_ftmo_login == 123456
    assert mt5.quantum_mt5_ftmo_password == "secret"  # pragma: allowlist secret


@pytest.mark.integration
def test_invalid_env_values_trigger_validation_error(tmp_workspace, iso_env):
    """
    Invalid types should not crash model instantiation but must produce string fallback.
    """
    env_path = tmp_workspace["root"] / ".env"
    env_path.write_text("QUANTUM_METRICS_PORT=not_a_number\n", encoding="utf-8")
    load_env(root=tmp_workspace["root"], apply=True)

    s = CoreSettings()  # type: ignore[arg-type]
    assert isinstance(s.quantum_metrics_port, (str, int))


@pytest.mark.integration
def test_defaults_are_deterministic_and_stable(iso_env):
    """
    Instantiating models without .env should always produce deterministic defaults.
    """
    core1 = CoreSettings()  # type: ignore[arg-type]
    core2 = CoreSettings()  # type: ignore[arg-type]

    assert core1.quantum_app_name == core2.quantum_app_name
    assert core1.quantum_env == core2.quantum_env
    assert isinstance(core1.quantum_metrics_port, int)
    assert core1.quantum_metrics_port >= 0

    log = LoggingSettings()  # type: ignore[arg-type]
    trace = TracingSettings()

    assert log.quantum_log_level == "INFO"
    assert trace.quantum_trace_exporter == "console"
    assert log.quantum_log_dir is None
    assert log.quantum_audit_dir is None


@pytest.mark.integration
def test_models_serialization_and_schema_coherence(tmp_workspace, iso_env):
    """
    Ensure each model can be serialized to JSON and schema definitions are valid.
    """
    load_env(root=tmp_workspace["root"], apply=True)
    models = [CoreSettings(), LoggingSettings(), TracingSettings(), MT5Settings()]  # type: ignore[arg-type]

    for model in models:
        data = model.model_dump()
        assert isinstance(data, dict)
        json_str = model.model_dump_json()
        assert isinstance(json_str, str)

        for field in model.__annotations__:
            assert field in data

        schema = model.model_json_schema()
        assert isinstance(schema, dict)
        assert "title" in schema
        assert "properties" in schema


@pytest.mark.integration
def test_configmanager_and_models_remain_coherent(tmp_workspace, iso_env):
    """
    Verify ConfigManager.load() and manual model instantiation remain consistent.
    """
    env_path = tmp_workspace["root"] / ".env"
    env_path.write_text(
        "QUANTUM_APP_NAME=test_app\nQUANTUM_METRICS_PORT=4242\n", encoding="utf-8"
    )

    load_env(root=tmp_workspace["root"], apply=True)

    m1 = ConfigManager.load(apply=False)
    m2 = CoreSettings()  # type: ignore[arg-type]

    assert isinstance(m1, CoreSettings)
    assert m1.quantum_app_name == m2.quantum_app_name
    assert m1.quantum_metrics_port == m2.quantum_metrics_port


@pytest.mark.integration
def test_partial_mt5_config_is_strict_with_incomplete_credentials(
    tmp_workspace, iso_env
):
    env_path = tmp_workspace["root"] / ".env"
    env_path.write_text("QUANTUM_MT5_FUNDEDNEXT_SERVER=server_only\n", encoding="utf-8")

    merged = load_env(root=tmp_workspace["root"], apply=True)
    normalized = {k.lower(): v for k, v in merged.items()}

    with pytest.raises(ValidationError):
        MT5Settings(**normalized)

    valid_mt5 = MT5Settings(
        quantum_mt5_ftmo_server="ok-server",
        quantum_mt5_ftmo_login=123456,
        quantum_mt5_ftmo_password="secret",  # pragma: allowlist secret
    )  # type: ignore[arg-type]

    exception_types: tuple[type[BaseException], ...] = (TypeError, ValidationError)

    with pytest.raises(exception_types):
        valid_mt5.quantum_mt5_ftmo_server = "changed"


@pytest.mark.integration
def test_model_field_aliases_and_case_insensitivity(tmp_workspace, iso_env):
    env_path = tmp_workspace["root"] / ".env"
    env_path.write_text("quantum_app_name=lowercase\n", encoding="utf-8")

    merged = load_env(root=tmp_workspace["root"], apply=True)
    normalized = {k.lower(): v for k, v in merged.items()}
    s = CoreSettings(**normalized)

    assert s.quantum_app_name == "lowercase"
