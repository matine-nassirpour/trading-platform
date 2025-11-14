import json
import logging

from contextlib import suppress
from typing import Any, Final, cast

from opentelemetry.trace import get_current_span
from pydantic import ValidationError

from quantum.infrastructure.observability.logging.diagnostics_logger import (
    DIAGNOSTIC_LOGGER,
)
from quantum.infrastructure.observability.logging.exception_processor import (
    ExceptionProcessor,
)
from quantum.infrastructure.observability.logging.models.factory import from_log_record
from quantum.infrastructure.observability.logging.models.log_payload_v1 import (
    LogPayloadV1,
)
from quantum.infrastructure.observability.logging.models.severity_map import (
    SEVERITY_MAP,
)
from quantum.infrastructure.observability.metrics.collectors.health_collector import (
    logging_schema_validation_errors_total,
)
from quantum.infrastructure.time.format_utils import now_mono_ms, to_rfc3339_ms

# ╭────────────────────────────────────────────────────────────────────────────╮
# │ Constants                                                                  │
# ╰────────────────────────────────────────────────────────────────────────────╯
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

    with suppress(Exception):
        trace_id = f"{int(getattr(sc, 'trace_id', 0)):032x}"
        span_id = f"{int(getattr(sc, 'span_id', 0)):016x}"

    # Sampling flag
    tf = getattr(sc, "trace_flags", None)
    sampled: bool | None = None
    if tf is not None:
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

    def __init__(self, instance_id: str) -> None:
        super().__init__()
        self._instance_id = instance_id

    def format(self, record: logging.LogRecord) -> str:
        trace_id, span_id, is_sampled = _extract_trace_context()

        ts_unix_ms = int(record.created * 1000)
        ts_mono_ms = getattr(record, "ts_monotonic_ms", now_mono_ms())

        attrs = self._extract_attrs(record)
        exception_block = ExceptionProcessor.extract(record)

        overrides = {
            "timestamp": to_rfc3339_ms(record.created),
            "ts_unix_ms": ts_unix_ms,
            "ts_monotonic_ms": ts_mono_ms,
            "env": getattr(record, "env", None),
            "instance": self._instance_id,
            "service_name": getattr(record, "service_name", None),
            "service_version": getattr(record, "service_version", None),
            "service_namespace": getattr(record, "service_namespace", None),
            "trace_id": trace_id,
            "span_id": span_id,
            "sampled": is_sampled,
            "attrs": attrs,
            **exception_block,
        }

        try:
            model: LogPayloadV1 = from_log_record(record, **overrides)
            return model.to_clean_json()
        except ValidationError as e:
            DIAGNOSTIC_LOGGER.error(
                f"LogPayloadV1 validation failed: {e.__class__.__name__}"
            )
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
    # Internal Helpers
    # --------------------------------------------------------------------------
    @staticmethod
    def _filter_record_fields(record: logging.LogRecord) -> dict[str, Any]:
        """Filter out excluded or reserved fields."""
        return {
            k: v
            for k, v in record.__dict__.items()
            if k not in _EXCLUDED_STD_FIELDS
            and k not in {"service_name", "service_version", "service_namespace", "env"}
        }

    @staticmethod
    def _normalize_field(key: str, value: Any, attrs: dict[str, Any]) -> None:
        """Normalize special cases: exception blocks and embedded attrs."""
        if key == "exception":
            try:
                if isinstance(value, dict):
                    attrs["exception_obj"] = value
                elif value is not None:
                    attrs["exception_text"] = str(value)
            except Exception:
                logging.getLogger(__name__).debug(
                    "Failed to normalize exception", exc_info=True
                )
        elif key == "attrs" and isinstance(value, dict):
            attrs.update(value)
        else:
            attrs[key] = value

    def _extract_attrs(self, record: logging.LogRecord) -> dict[str, Any]:
        """Extract and sanitize custom attributes from a LogRecord."""
        attrs: dict[str, Any] = {}
        for k, v in self._filter_record_fields(record).items():
            self._normalize_field(k, v, attrs)
        return cast(dict[str, Any], _json_sanitize(attrs))

    def _build_fallback_payload(
        self,
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
            "instance": self._instance_id,
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
            "exception": overrides["exception"],
            "exception_type": overrides["exception_type"],
            "exception_message": overrides["exception_message"],
            "exception_stacktrace": overrides["exception_stacktrace"],
            "attrs": attrs,
        }

        logging_schema_validation_errors_total.inc()

        return json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
