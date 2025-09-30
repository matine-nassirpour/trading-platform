import json
import logging
import socket
from typing import Any

from opentelemetry.trace import get_current_span
from pydantic import ValidationError

from quantum.adapters.telemetry.context.run_id import get_run_id
from quantum.adapters.telemetry.correlation.correlation_id import get_correlation_id
from quantum.adapters.telemetry.logging.models.log_payload_v1 import LogPayloadV1
from quantum.foundation.time.rfc3339 import from_unix_s_to_rfc3339_ms, now_mono_ms

INSTANCE_ID = socket.gethostname()
EXCLUDED_STD_FIELDS = {
    "args",
    "asctime",
    "created",
    "exc_info",
    "exc_text",
    "filename",
    "funcName",
    "levelno",
    "lineno",
    "module",
    "msecs",
    "message",
    "msg",
    "name",
    "pathname",
    "process",
    "processName",
    "relativeCreated",
    "stack_info",
    "thread",
    "threadName",
    "env",
}


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        # OpenTelemetry context
        span = get_current_span()
        span_context = span.get_span_context()
        trace_id = (
            format(span_context.trace_id, "032x") if span_context.trace_id else None
        )
        span_id = format(span_context.span_id, "016x") if span_context.span_id else None
        is_sampled = span_context.trace_flags.sampled

        correlation_id = get_correlation_id()
        run_id = get_run_id()
        message = record.getMessage()
        now_ms = int(record.created * 1000)
        mono_ms = getattr(record, "ts_monotonic_ms", now_mono_ms())

        payload_dict: dict[str, Any] = {
            "timestamp": from_unix_s_to_rfc3339_ms(record.created),
            "ts_unix_ms": now_ms,
            "ts_monotonic_ms": mono_ms,
            "level": record.levelname,
            "logger": record.name,
            "message": message,
            "env": getattr(record, "env", "unknown"),
            "instance": INSTANCE_ID,
            "trace_id": trace_id,
            "span_id": span_id,
            "sampled": is_sampled,
            "correlation_id": correlation_id,
            "run_id": run_id,
            "log_schema_version": "v1",
            "attrs": {},
        }

        # Include exception info if available
        if record.exc_info:
            exception_msg = self.formatException(record.exc_info)
            payload_dict["exception"] = exception_msg

        # Route all non-standard extras to attrs
        attrs = payload_dict["attrs"]
        for key, value in record.__dict__.items():
            if key in EXCLUDED_STD_FIELDS:
                continue
            if key == "attrs" and isinstance(value, dict):
                attrs.update(value)
                continue
            if key in payload_dict:
                continue
            attrs[key] = value

        try:
            model = LogPayloadV1.model_validate(payload_dict)
            return model.to_clean_json()
        except ValidationError as e:
            # Fallback JSON
            payload_dict["log_schema_version"] = "fallback"
            payload_dict["validation_error"] = str(e)
            return json.dumps(payload_dict, ensure_ascii=False, separators=(",", ":"))
