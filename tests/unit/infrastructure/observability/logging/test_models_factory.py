from __future__ import annotations

import logging
from typing import Any

from quantum.infrastructure.observability.logging.models.factory import from_log_record


def _make_record(
    *,
    name: str = "x.logger",
    level: int = logging.WARNING,
    msg: str = "hello %s",
    args: tuple[Any, ...] = ("world",),
) -> logging.LogRecord:
    return logging.LogRecord(
        name=name,
        level=level,
        pathname=__file__,
        lineno=123,
        msg=msg,
        args=args,
        exc_info=None,
    )


def test_from_log_record_maps_severity_and_builds_payload():
    rec = _make_record()
    payload = from_log_record(
        rec,
        # horodatage/monotonic fournis par le formatter en prod → override ici
        timestamp="2025-10-07T12:00:00.000Z",
        ts_unix_ms=1_695_680_000_000,
        ts_monotonic_ms=123456,
        env="dev",
        instance="desk-01",
        service_name="python_core",
        service_version="0.1.0+dev",
        service_namespace="quantum",
        # Contexte de trace valide (hex strict)
        trace_id="0" * 32,
        span_id="a" * 16,
        sampled=True,
        correlation_id="11111111-1111-4111-8111-111111111111",
        run_id="22222222-2222-4222-8222-222222222222",
        attrs={"k": "v", "n": 1},
    )

    # mapping WARNING -> WARN (OTel)
    assert payload.level == "WARN"
    # WARNING -> 13 dans notre mapping
    assert payload.severity_number == 13

    assert payload.logger == "x.logger"
    assert payload.message == "hello world"

    assert payload.env == "dev"
    assert payload.instance == "desk-01"
    assert payload.service_name == "python_core"
    assert payload.service_version == "0.1.0+dev"
    assert payload.service_namespace == "quantum"

    assert payload.trace_id == "0" * 32
    assert payload.span_id == "a" * 16
    assert payload.sampled is True
    assert payload.correlation_id.endswith("1111")
    assert payload.run_id.endswith("2222")

    assert payload.attrs["k"] == "v" and payload.attrs["n"] == 1

    # JSON propre sérialisable
    js = payload.to_clean_json()
    assert '"schema":"quantum.log"' in js
    assert '"log_schema_version":"v1"' in js
