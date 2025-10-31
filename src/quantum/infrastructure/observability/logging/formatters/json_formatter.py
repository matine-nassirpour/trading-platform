import json
import logging
import socket
from contextlib import suppress
from typing import Any, Final

from opentelemetry.trace import get_current_span
from pydantic import ValidationError

from quantum.infrastructure.config.runtime.manager import ConfigManager
from quantum.infrastructure.observability.context.run_id import get_run_id
from quantum.infrastructure.observability.logging.models.factory import from_log_record
from quantum.infrastructure.observability.logging.models.log_payload_v1 import (
    LogPayloadV1,
)
from quantum.infrastructure.observability.logging.models.severity_map import (
    SEVERITY_MAP,
)
from quantum.infrastructure.observability.tracing.correlation.correlation_id import (
    get_correlation_id,
)
from quantum.infrastructure.time.format_utils import now_mono_ms, to_rfc3339_ms

# ╭────────────────────────────────────────────────────────────────────────────╮
# │ Constants                                                                  │
# ╰────────────────────────────────────────────────────────────────────────────╯
_CORE_SETTINGS: Final = ConfigManager.load()
_INSTANCE_ID: Final[str] = _CORE_SETTINGS.quantum_instance_id or socket.gethostname()
_EXCLUDED_STD_FIELDS: Final[set[str]] = {
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


# ╭────────────────────────────────────────────────────────────────────────────╮
# │ Internal Helpers                                                           │
# ╰────────────────────────────────────────────────────────────────────────────╯
def _json_sanitize(obj: Any) -> Any:
    """
    Recursively convert arbitrary objects into JSON-safe representations.

    Strategies:
        - bytes   → short repr()
        - sets    → lists
        - unknown → str() truncated to max length
    """
    _MAX_STR_LEN = 10_000

    if obj is None or isinstance(obj, (bool, int, float)):
        return obj
    if isinstance(obj, str):
        return obj if len(obj) <= _MAX_STR_LEN else obj[:_MAX_STR_LEN] + "…"
    if isinstance(obj, (list, tuple, set)):
        return [_json_sanitize(x) for x in obj]
    if isinstance(obj, dict):
        return {str(k): _json_sanitize(v) for k, v in obj.items()}
    if isinstance(obj, bytes):
        return repr(obj[:64]) + ("… (truncated)" if len(obj) > 64 else "")
    s = str(obj)
    return s[:_MAX_STR_LEN] + ("…" if len(s) > _MAX_STR_LEN else "")


def _extract_trace_context() -> tuple[str | None, str | None, bool | None]:
    """
    Extracts (trace_id, span_id, sampled) from the current OpenTelemetry span,
    robust to cross-version API differences.
    """
    try:
        span = get_current_span()
        sc = span.get_span_context()
    except (AttributeError, TypeError):
        return None, None, None

    try:
        is_valid = bool(getattr(sc, "is_valid", False))
    except Exception:
        is_valid = False

    if not is_valid:
        return None, None, None

    try:
        trace_id = f"{int(getattr(sc, 'trace_id', 0)):032x}"
        span_id = f"{int(getattr(sc, 'span_id', 0)):016x}"
    except Exception:
        trace_id = span_id = None

    # Sampling flag
    tf = getattr(sc, "trace_flags", None)
    sampled: bool | None = None
    if tf is None:
        sampled = None
    else:
        attr = getattr(tf, "sampled", None)
        if isinstance(attr, bool):
            sampled = attr
        elif callable(attr):
            with suppress(Exception):
                sampled = bool(attr())
        else:
            with suppress(Exception):
                sampled = bool(int(tf) & 0x01)

    return trace_id, span_id, sampled


# ╭────────────────────────────────────────────────────────────────────────────╮
# │ Formatter                                                                  │
# ╰────────────────────────────────────────────────────────────────────────────╯
class JsonFormatter(logging.Formatter):
    """
    Formats log records into structured JSON lines conforming to the Quantum schema.

    On ValidationError, falls back to a simplified safe schema while emitting
    a health metric for schema validation failures.
    """

    def format(self, record: logging.LogRecord) -> str:
        trace_id, span_id, is_sampled = _extract_trace_context()

        ts_unix_ms = int(record.created * 1000)
        ts_mono_ms = getattr(record, "ts_monotonic_ms", now_mono_ms())

        attrs = self._extract_attrs(record)
        exception_block = self._extract_exception_block(record)

        overrides = {
            # timestamps
            "timestamp": to_rfc3339_ms(record.created),
            "ts_unix_ms": ts_unix_ms,
            "ts_monotonic_ms": ts_mono_ms,
            # resource/env
            "env": getattr(record, "env", "unknown"),
            "instance": _INSTANCE_ID,
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
            # Exception data
            **exception_block,
        }

        try:
            model: LogPayloadV1 = from_log_record(record, **overrides)
            return model.to_clean_json()
        except ValidationError as e:
            return self._build_fallback_payload(
                record,
                overrides,
                e,
                ts_unix_ms,
                ts_mono_ms,
                trace_id,
                span_id,
                is_sampled,
                attrs,
            )

    # --------------------------------------------------------------------------
    # Extractors
    # --------------------------------------------------------------------------
    @staticmethod
    def _extract_attrs(record: logging.LogRecord) -> dict[str, Any]:
        """Extracts and sanitizes custom attributes from a LogRecord."""
        attrs: dict[str, Any] = {}
        for k, v in record.__dict__.items():
            if k in _EXCLUDED_STD_FIELDS:
                continue
            if k == "exception":
                try:
                    if isinstance(v, dict):
                        attrs["exception_obj"] = v
                    elif v is not None:
                        attrs["exception_text"] = str(v)
                except Exception:
                    pass
                continue
            if k in {"service_name", "service_version", "service_namespace", "env"}:
                continue
            if k == "attrs" and isinstance(v, dict):
                attrs.update(v)
                continue
            attrs[k] = v
        return _json_sanitize(attrs)

    def _extract_exception_block(self, record: logging.LogRecord) -> dict[str, Any]:
        """Builds a structured exception block from exc_info if present."""
        exception_text = exception_type = exception_message = exception_stacktrace = (
            None
        )
        if record.exc_info:
            try:
                etype, evalue, _tb = record.exc_info
                exception_type = getattr(etype, "__name__", str(etype))
                exception_message = str(evalue) if evalue is not None else None
                exception_stacktrace = self.formatException(record.exc_info)
                exception_text = exception_stacktrace
            except Exception:
                exception_text = "exception formatting failed"
                exception_type = "Exception"
        return {
            "exception": exception_text,
            "exception_type": exception_type,
            "exception_message": exception_message,
            "exception_stacktrace": exception_stacktrace,
        }

    # --------------------------------------------------------------------------
    # Fallback payload
    # --------------------------------------------------------------------------
    @staticmethod
    def _build_fallback_payload(
        record: logging.LogRecord,
        overrides: dict[str, Any],
        e: ValidationError,
        ts_unix_ms: int,
        ts_mono_ms: int,
        trace_id: str | None,
        span_id: str | None,
        is_sampled: bool | None,
        attrs: dict[str, Any],
    ) -> str:
        """Builds a simplified JSON payload when schema validation fails."""
        sev_text, sev_num = SEVERITY_MAP.get(record.levelno, ("INFO", 9))

        payload = {
            "timestamp": overrides["timestamp"],
            "ts_unix_ms": ts_unix_ms,
            "ts_monotonic_ms": ts_mono_ms,
            "level": sev_text,
            "severity_number": sev_num,
            "logger": record.name,
            "message": record.getMessage(),
            "env": overrides["env"],
            "instance": _INSTANCE_ID,
            "service_name": overrides["service_name"],
            "service_version": overrides["service_version"],
            "service_namespace": overrides["service_namespace"],
            "trace_id": trace_id,
            "span_id": span_id,
            "sampled": is_sampled,
            "correlation_id": overrides["correlation_id"],
            "run_id": overrides["run_id"],
            "schema": "quantum.log",
            "log_schema_version": "fallback",
            "validation_error": str(e),
            "attrs": attrs,
            "exception": overrides["exception"],
            "exception_type": overrides["exception_type"],
            "exception_message": overrides["exception_message"],
            "exception_stacktrace": overrides["exception_stacktrace"],
        }

        with suppress(ModuleNotFoundError, AttributeError, ValueError, RuntimeError):
            from quantum.infrastructure.observability.metrics.collectors.health_collector import (
                logging_schema_validation_errors_total,
            )

            logging_schema_validation_errors_total.inc()

        return json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
