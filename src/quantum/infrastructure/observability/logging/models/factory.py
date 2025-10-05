from logging import LogRecord
from typing import cast

from .log_payload_v1 import LogPayloadV1, SeverityText

_PY_TO_OTEL = {
    0: ("TRACE", 1),  # logging.NOTSET
    10: ("DEBUG", 5),
    20: ("INFO", 9),
    30: ("WARN", 13),
    40: ("ERROR", 17),
    50: ("FATAL", 21),
}


def from_log_record(record: LogRecord, **overrides) -> LogPayloadV1:
    sev_text, sev_num = _PY_TO_OTEL.get(record.levelno, ("INFO", 9))
    sev_text = cast(SeverityText, sev_text)
    extra_attrs = dict(overrides.get("attrs", {}))

    payload = LogPayloadV1(
        timestamp=overrides.get("timestamp"),
        ts_unix_ms=overrides.get("ts_unix_ms"),
        ts_monotonic_ms=overrides.get("ts_monotonic_ms"),
        level=sev_text,
        severity_number=sev_num,
        logger=record.name,
        message=record.getMessage(),
        env=overrides.get("env", "dev"),
        instance=overrides.get("instance", "localhost"),
        service_name=overrides.get("service_name"),
        service_version=overrides.get("service_version"),
        service_namespace=overrides.get("service_namespace"),
        trace_id=overrides.get("trace_id"),
        span_id=overrides.get("span_id"),
        sampled=overrides.get("sampled"),
        correlation_id=overrides.get("correlation_id"),
        run_id=overrides.get("run_id"),
        exception=overrides.get("exception"),
        schema_name="quantum.log",
        log_schema_version="v1",
        attrs=extra_attrs,
    )
    return payload
