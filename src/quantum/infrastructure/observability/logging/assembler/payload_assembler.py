from __future__ import annotations

import logging

from pydantic import ValidationError

from quantum.infrastructure.observability.logging.core.metrics import define_counter
from quantum.infrastructure.observability.logging.core.trace_context import (
    extract_trace_context,
)
from quantum.infrastructure.observability.logging.models.factory import from_log_record
from quantum.infrastructure.time.format_utils import now_mono_ms, to_rfc3339_ms

_schema_validation_errors = define_counter("schema_validation_errors")


class PayloadAssembler:
    """Pure SRP: assemble a validated LogPayloadV1 instance for a LogRecord."""

    @staticmethod
    def build(record: logging.LogRecord, instance_id: str):
        trace_id, span_id, sampled = extract_trace_context()

        ts_unix_ms = int(record.created * 1000)
        ts_mono_ms = getattr(record, "ts_monotonic_ms", now_mono_ms())

        overrides = {
            "timestamp": to_rfc3339_ms(record.created),
            "ts_unix_ms": ts_unix_ms,
            "ts_monotonic_ms": ts_mono_ms,
            "env": getattr(record, "env", None),
            "instance": instance_id,
            "service_name": getattr(record, "service_name", None),
            "service_version": getattr(record, "service_version", None),
            "service_namespace": getattr(record, "service_namespace", None),
            "trace_id": trace_id,
            "span_id": span_id,
            "sampled": sampled,
            "correlation_id": getattr(record, "correlation_id", None),
            "run_id": getattr(record, "run_id", None),
            "attrs": getattr(record, "attrs", {}),
        }

        try:
            model = from_log_record(record, **overrides)
            return model
        except ValidationError:
            _schema_validation_errors.inc()
            raise
