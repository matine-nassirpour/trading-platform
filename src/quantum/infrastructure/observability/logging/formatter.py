import json
import logging
import socket
from contextlib import suppress
from typing import Any

from opentelemetry.trace import get_current_span
from pydantic import ValidationError

from quantum.infrastructure.observability.logging.models.factory import from_log_record
from quantum.infrastructure.observability.logging.models.log_payload_v1 import (
    LogPayloadV1,
)
from quantum.shared.context.run_id import get_run_id
from quantum.shared.correlation.correlation_id import get_correlation_id
from quantum.shared.time.rfc3339 import from_unix_s_to_rfc3339_ms, now_mono_ms

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


def _json_sanitize(obj: Any) -> Any:
    """
    Recursively converts to JSON-safe types.

    - bytes -> base64-like str (here: short repr)
    - set/tuple -> list
    - unknown objects -> truncated str(obj)
    """
    max_str = 10_000
    if obj is None or isinstance(obj, (bool, int, float)):
        return obj
    if isinstance(obj, str):
        return obj if len(obj) <= max_str else obj[:max_str] + "…"
    if isinstance(obj, (list, tuple, set)):
        return [_json_sanitize(x) for x in obj]
    if isinstance(obj, dict):
        return {str(k): _json_sanitize(v) for k, v in obj.items()}
    if isinstance(obj, bytes):
        return repr(obj[:64]) + ("… (truncated)" if len(obj) > 64 else "")
    return str(obj)[:max_str] + ("…" if len(str(obj)) > max_str else "")


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        # OTEL context
        span = get_current_span()
        sc = span.get_span_context()
        is_valid = getattr(sc, "is_valid", False)
        trace_id = format(sc.trace_id, "032x") if is_valid else None
        span_id = format(sc.span_id, "016x") if is_valid else None
        is_sampled = sc.trace_flags.sampled if is_valid else None

        # Timestamps
        ts_unix_ms = int(record.created * 1000)
        ts_mono_ms = getattr(record, "ts_monotonic_ms", now_mono_ms())

        # Collect extras → attrs
        attrs: dict[str, Any] = {}
        for k, v in record.__dict__.items():
            if k in EXCLUDED_STD_FIELDS:
                continue
            # Avoid conflict with the top-level "exception" field (string expected)
            if k == "exception":
                try:
                    if isinstance(v, dict):
                        attrs["exception_obj"] = v  # structured copy on the attrs side
                    elif v is not None:
                        attrs["exception_text"] = str(v)
                except Exception:
                    pass
                continue
            if k in {"service_name", "service_version", "service_namespace", "env"}:
                # These fields are passed via overrides, do not duplicate in attrs
                continue
            if k == "attrs" and isinstance(v, dict):
                attrs.update(v)
                continue
            attrs[k] = v
        attrs = _json_sanitize(attrs)

        overrides = {
            # timestamps
            "timestamp": from_unix_s_to_rfc3339_ms(record.created),
            "ts_unix_ms": ts_unix_ms,
            "ts_monotonic_ms": ts_mono_ms,
            # resource/env
            "env": getattr(record, "env", "unknown"),
            "instance": INSTANCE_ID,
            "service_name": getattr(record, "service_name", None),
            "service_version": getattr(record, "service_version", None),
            "service_namespace": getattr(record, "service_namespace", None),
            # correlation
            "trace_id": trace_id,
            "span_id": span_id,
            "sampled": is_sampled,
            "correlation_id": get_correlation_id(),
            "run_id": get_run_id(),
            # attrs
            "attrs": attrs,
        }

        try:
            # Centralise : severity_number + exception structuré
            model: LogPayloadV1 = from_log_record(record, **overrides)
            return model.to_clean_json()
        except ValidationError as e:
            # Minimal but safe JSON fallback
            payload_dict = {
                "timestamp": overrides["timestamp"],
                "ts_unix_ms": ts_unix_ms,
                "ts_monotonic_ms": ts_mono_ms,
                "level": record.levelname,
                "logger": record.name,
                "message": record.getMessage(),
                "env": overrides["env"],
                "instance": INSTANCE_ID,
                "trace_id": trace_id,
                "span_id": span_id,
                "sampled": is_sampled,
                "correlation_id": overrides["correlation_id"],
                "run_id": overrides["run_id"],
                "schema": "quantum.log",
                "log_schema_version": "fallback",
                "validation_error": str(e),
                "attrs": attrs,
            }

            with suppress(
                ModuleNotFoundError, AttributeError, ValueError, RuntimeError
            ):
                from quantum.infrastructure.observability.metrics.health import (
                    logging_schema_validation_errors_total,
                )

                logging_schema_validation_errors_total.inc()

            return json.dumps(payload_dict, ensure_ascii=False, separators=(",", ":"))
