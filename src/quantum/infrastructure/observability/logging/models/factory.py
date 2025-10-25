from logging import LogRecord
from typing import Any, cast

from .log_payload_v1 import LogPayloadV1, SeverityText
from .severity_map import SEVERITY_MAP


def from_log_record(record: LogRecord, **overrides) -> LogPayloadV1:
    """
    Transforms a Python LogRecord into a validated LogPayloadV1 instance.

    Args:
        record: The native `logging.LogRecord` emitted by Python's logging system.
        **overrides: Optional keyword arguments to override or inject contextual
            values into the final payload. Common keys include:
                - timestamp, ts_unix_ms, ts_monotonic_ms
                - env, instance, service_name, service_version, service_namespace
                - trace_id, span_id, sampled
                - correlation_id, run_id
                - exception, exception_type, exception_message, exception_stacktrace
                - attrs (dict[str, Any])

    Returns:
        LogPayloadV1: A fully validated, immutable structured log payload.

    Raises:
        pydantic.ValidationError: If the payload fails schema validation.
    """
    sev_text, sev_num = SEVERITY_MAP.get(record.levelno, ("INFO", 9))
    sev_text = cast(SeverityText, sev_text)

    extra_attrs: dict[str, Any] = dict(overrides.get("attrs", {}))

    return LogPayloadV1(
        # ─── Timestamps
        timestamp=overrides.get("timestamp"),
        ts_unix_ms=overrides.get("ts_unix_ms"),
        ts_monotonic_ms=overrides.get("ts_monotonic_ms"),
        # ─── Severity
        level=sev_text,
        severity_number=sev_num,
        # ─── Source
        logger=record.name,
        message=record.getMessage(),
        # ─── Environment
        env=overrides.get("env", "dev"),
        instance=overrides.get("instance", "localhost"),
        service_name=overrides.get("service_name"),
        service_version=overrides.get("service_version"),
        service_namespace=overrides.get("service_namespace"),
        # ─── Correlation
        trace_id=overrides.get("trace_id"),
        span_id=overrides.get("span_id"),
        sampled=overrides.get("sampled"),
        correlation_id=overrides.get("correlation_id"),
        run_id=overrides.get("run_id"),
        # ─── exceptions
        exception=overrides.get("exception"),
        exception_type=overrides.get("exception_type"),
        exception_message=overrides.get("exception_message"),
        exception_stacktrace=overrides.get("exception_stacktrace"),
        # ─── schema
        schema_name="quantum.log",
        log_schema_version="v1",
        # ─── attributes
        attrs=extra_attrs,
    )
