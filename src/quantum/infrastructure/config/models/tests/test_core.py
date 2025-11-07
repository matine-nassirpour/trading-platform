import pytest

from pydantic import ValidationError

from quantum.infrastructure.config.models.core import CoreSettings


def test_core_settings_defaults_are_safe():
    """Defaults must be consistent, non-null, and safe for any environment."""
    s = CoreSettings()  # type: ignore[arg-type]
    assert isinstance(s.quantum_app_name, str)
    assert s.quantum_env in ("dev", "test", "staging", "prod")
    assert s.quantum_metrics_port >= 0
    assert s.quantum_exec_timeout > 0


def test_core_settings_env_loading_via_env_prefix(monkeypatch):
    """Environment variables with QUANTUM_ prefix must populate settings."""
    monkeypatch.setenv("QUANTUM_APP_NAME", "quantum_test_app")
    monkeypatch.setenv("QUANTUM_ENV", "staging")
    s = CoreSettings()  # type: ignore[arg-type]
    assert s.quantum_app_name == "quantum_test_app"
    assert s.quantum_env == "staging"


def test_core_settings_validation_rejects_invalid_enum():
    """Invalid environment values must raise a validation error."""
    with pytest.raises(ValidationError):
        CoreSettings(quantum_env="invalid_env")  # type: ignore[arg-type]


def test_core_settings_serialization_roundtrip():
    """dict() / parse_obj() roundtrip must preserve field values exactly."""
    original = CoreSettings(
        quantum_app_name="quantum",
        quantum_env="test",
        quantum_ns="q",
        quantum_metrics_port=1234,
    )  # type: ignore[arg-type]
    payload = original.model_dump()
    clone = CoreSettings.model_validate(payload)
    assert clone == original
