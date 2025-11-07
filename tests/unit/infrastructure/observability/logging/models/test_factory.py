from __future__ import annotations

import logging

import pytest

from quantum.infrastructure.observability.logging.models.factory import from_log_record
from tests.support.factories import make_record


@pytest.mark.unit
def test_from_log_record_maps_severity_and_builds_payload():
    """
    Given a LogRecord with message formatting, WARNING level and rich context
    When building a log payload via from_log_record
    Then severity mapping/numbers are correct, fields are propagated, and JSON is clean
    """
    # Arrange: create a LogRecord and set args after creation (getMessage will format it)
    rec: logging.LogRecord = make_record(
        name="x.logger",
        level=logging.WARNING,
        msg="hello %s",
    )
    # Set args post-creation to exercise getMessage() path
    rec.args = ("world",)

    # Act
    payload = from_log_record(
        rec,
        # timestamps/monotonic provided by the formatter in prod → override here for determinism
        timestamp="2025-10-07T12:00:00.000Z",
        ts_unix_ms=1_695_680_000_000,
        ts_monotonic_ms=123456,
        env="dev",
        instance="desk-01",
        service_name="python_core",
        service_version="0.1.0+dev",
        service_namespace="quantum",
        # Strict hex trace context
        trace_id="0" * 32,
        span_id="a" * 16,
        sampled=True,
        correlation_id="11111111-1111-4111-8111-111111111111",
        run_id="22222222-2222-4222-8222-222222222222",
        attrs={"k": "v", "n": 1},
    )

    # Assert: OTel mapping (WARNING → WARN, severity number domain)
    assert payload.level == "WARN"
    assert payload.severity_number == 13  # expected mapping for WARNING

    # Assert: message and logger name
    assert payload.logger == "x.logger"
    assert payload.message == "hello world"

    # Assert: resource/context fields
    assert payload.env == "dev"
    assert payload.instance == "desk-01"
    assert payload.service_name == "python_core"
    assert payload.service_version == "0.1.0+dev"
    assert payload.service_namespace == "quantum"

    # Assert: tracing & correlation
    assert payload.trace_id == "0" * 32
    assert payload.span_id == "a" * 16
    assert payload.sampled is True
    assert payload.correlation_id.endswith("1111")
    assert payload.run_id.endswith("2222")

    # Assert: attrs copied as-is
    assert payload.attrs["k"] == "v" and payload.attrs["n"] == 1

    # Assert: JSON is clean/serializable and includes schema/version markers
    js = payload.to_clean_json()
    assert '"schema":"quantum.log"' in js
    assert '"log_schema_version":"v1"' in js
