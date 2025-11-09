import pytest

from quantum.infrastructure.config.validators.rules import (
    CompressionValidator,
    EnvironmentValidator,
    LogLevelValidator,
    OtlpProtocolValidator,
    TimezoneValidator,
)


@pytest.mark.verification
@pytest.mark.parametrize(
    "value,expected",
    [("DEV", "dev"), ("prod", "prod"), ("Staging", "staging"), (None, "dev")],
)
def test_environment_validator_accepts_valid(value, expected):
    v = EnvironmentValidator()
    result = v(value)

    assert result.ok
    assert result.value == expected


@pytest.mark.verification
def test_environment_validator_rejects_invalid():
    v = EnvironmentValidator()
    result = v("wrong-env")
    assert not result.ok
    assert "Invalid" in result.message


@pytest.mark.verification
@pytest.mark.parametrize("value", ["INFO", "debug", "CRITICAL"])
def test_log_level_validator_accepts_valid(value):
    v = LogLevelValidator()
    res = v(value)
    assert res.ok
    assert res.value in {"INFO", "DEBUG", "WARNING", "ERROR", "CRITICAL"}


@pytest.mark.verification
def test_log_level_validator_rejects_unknown():
    v = LogLevelValidator()
    res = v("unknown")
    assert not res.ok
    assert "Invalid log level" in res.message


@pytest.mark.verification
@pytest.mark.parametrize("value", ["utc", "local", "UTC"])
def test_timezone_validator_valid(value):
    v = TimezoneValidator()
    res = v(value)
    assert res.ok
    assert res.value.lower() in {"utc", "local"}


@pytest.mark.verification
def test_timezone_validator_invalid():
    v = TimezoneValidator()
    res = v("mars")
    assert not res.ok


@pytest.mark.verification
@pytest.mark.parametrize("value,expected", [("grpc", "grpc"), ("http", "http")])
def test_otlp_protocol_validator_valid(value, expected):
    v = OtlpProtocolValidator()
    res = v(value)
    assert res.ok
    assert res.value == expected


@pytest.mark.verification
def test_otlp_protocol_validator_invalid_warns(caplog):
    v = OtlpProtocolValidator()
    res = v("invalid")
    assert res.ok
    assert res.value == "http"
    assert "Unsupported OTLP protocol" in caplog.text


@pytest.mark.verification
@pytest.mark.parametrize("value", ["gzip", "none"])
def test_compression_validator_valid(value):
    v = CompressionValidator()
    res = v(value)
    assert res.ok
    assert res.value == value


@pytest.mark.verification
def test_compression_validator_invalid():
    v = CompressionValidator()
    res = v("snappy")
    assert not res.ok
