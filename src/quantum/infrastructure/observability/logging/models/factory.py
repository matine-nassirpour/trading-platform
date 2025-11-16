from logging import LogRecord
from typing import Any

from ..exception_processor import EXCEPTION_FIELD_NAMES
from .log_payload_v1 import ExceptionBlock, LogPayloadV1
from .severity_map import canonical_severity


def from_log_record(record: LogRecord, **overrides: Any) -> LogPayloadV1:
    """Transforms a Python LogRecord into a validated LogPayloadV1 instance."""
    sev_text, sev_num = canonical_severity(record.levelno)

    extra_attrs: dict[str, Any] = dict(overrides.get("attrs", {}))

    exception_block = ExceptionBlock(
        **{name: overrides.get(name) for name in EXCEPTION_FIELD_NAMES}
    )

    payload_kwargs = {
        # Timestamps
        "timestamp": str(overrides["timestamp"]),
        "ts_unix_ms": overrides.get("ts_unix_ms"),
        "ts_monotonic_ms": overrides.get("ts_monotonic_ms"),
        # Severity (normalized)
        "level": sev_text,
        "severity_number": sev_num,
        # Logger + message
        "logger": record.name,
        "message": record.getMessage(),
        # Environment / resource
        "env": overrides.get("env"),
        "instance": overrides.get("instance"),
        "service_name": overrides.get("service_name"),
        "service_version": overrides.get("service_version"),
        "service_namespace": overrides.get("service_namespace"),
        # Correlation / tracing
        "trace_id": overrides.get("trace_id"),
        "span_id": overrides.get("span_id"),
        "sampled": overrides.get("sampled"),
        "correlation_id": overrides.get("correlation_id"),
        "run_id": overrides.get("run_id"),
        "attrs": extra_attrs,
        "exception_block": exception_block,
        # Schema metadata
        "schema_name": "quantum.log",
        "log_schema_version": "v1",
    }

    return LogPayloadV1(**payload_kwargs)
