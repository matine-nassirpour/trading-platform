import pytest
from pydantic import ValidationError

from quantum.infrastructure.config.models.tracing import TracingSettings


def test_tracing_settings_defaults_are_valid():
    """Default tracing config must be safe and within valid parameter ranges."""
    s = TracingSettings()
    assert s.quantum_trace_exporter in ("console", "otlp", "none")
    assert 0.0 <= s.quantum_trace_sample <= 1.0
    assert s.quantum_trace_otlp_compression in ("none", "gzip", "deflate")


def test_tracing_settings_rejects_invalid_protocol(caplog):
    """Invalid OTLP protocol must trigger fallback and warning, not crash."""
    with caplog.at_level("WARNING"):
        s = TracingSettings(quantum_trace_otlp_protocol="invalid")  # type: ignore[arg-type]

    assert any("Unsupported OTLP protocol" in r.message for r in caplog.records)
    assert s.quantum_trace_otlp_protocol == "http"


def test_tracing_settings_sample_bounds():
    """Sample rate outside [0, 1] must trigger validation error."""
    with pytest.raises(ValidationError):
        TracingSettings(quantum_trace_sample=1.5)
    with pytest.raises(ValidationError):
        TracingSettings(quantum_trace_sample=-0.1)
