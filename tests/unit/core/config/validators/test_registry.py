import pytest

from quantum.core.config.validators import (
    base,
    registry,
    rules,
    validate_field,
    validate_model,
)


def test_registry_register_defaults_contains_expected_rules():
    reg = registry.ValidatorRegistry()
    reg.register_defaults()
    ids = set(reg._registry.keys())

    for expected in (
        "core.runtime.environment",
        "core.logging.log_level",
        "core.logging.timezone",
        "core.tracing.otlp_protocol",
        "core.tracing.compression",
    ):
        assert expected in ids


def test_registry_rejects_duplicate_registration():
    reg = registry.ValidatorRegistry()
    reg.clear_registry()
    rule = rules.EnvironmentValidator()
    reg.register(rule)
    with pytest.raises(ValueError):
        reg.register(rule)


def test_validate_field_success(monkeypatch):
    reg = registry.ValidatorRegistry()
    reg.register_defaults()
    ctx = base.ValidationContext(field_name="quantum_env")

    result = reg.validate("core.runtime.environment", "dev", context=ctx)

    assert result.ok
    assert result.value == "dev"


def test_validate_field_failure(monkeypatch):
    with pytest.raises(ValueError) as exc:
        validate_field(
            "core.runtime.environment",
            "unknown",
            field="quantum_env",
            model="CoreSettings",
        )

    assert "Invalid environment" in str(exc.value)


def test_validate_model_integration(monkeypatch):
    dummy_values = {
        "environment": "dev",
        "log_level": "INFO",
        "otlp_protocol": "grpc",
    }

    res = validate_model("DummyModel", dummy_values)

    assert res["environment"] == "dev"
    assert res["log_level"] == "INFO"
    assert res["otlp_protocol"] == "grpc"
