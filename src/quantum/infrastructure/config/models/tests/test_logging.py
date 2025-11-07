import os

import pytest

from pydantic import ValidationError

from quantum.infrastructure.config.models.logging import LoggingSettings


def test_logging_settings_defaults_are_safe(tmp_path):
    """Default logging settings must define valid paths and thresholds."""
    s = LoggingSettings(quantum_log_dir=str(tmp_path), quantum_audit_dir=str(tmp_path))
    assert os.path.isdir(s.quantum_log_dir)
    assert os.path.isdir(s.quantum_audit_dir)
    assert s.quantum_log_max_bytes >= 0
    assert s.quantum_log_warn_bytes >= 0


def test_logging_settings_rejects_negative_sizes(tmp_path):
    """Negative log size limits must trigger validation error."""
    with pytest.raises(ValidationError):
        LoggingSettings(
            quantum_log_dir=str(tmp_path),
            quantum_audit_dir=str(tmp_path),
            quantum_log_max_bytes=-1,
        )


def test_logging_settings_roundtrip():
    """Roundtrip serialization/deserialization must preserve semantics."""
    s = LoggingSettings(
        quantum_log_dir="/tmp/logs",
        quantum_audit_dir="/tmp/audit",
        quantum_log_max_bytes=1024,
    )  # type: ignore[arg-type]
    clone = LoggingSettings.model_validate(s.model_dump())
    assert clone.quantum_log_dir == "/tmp/logs"
    assert clone.quantum_audit_dir == "/tmp/audit"
    assert clone.quantum_log_max_bytes == 1024
