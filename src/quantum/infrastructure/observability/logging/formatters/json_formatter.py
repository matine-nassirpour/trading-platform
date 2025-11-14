import logging

from typing import Any, Final, cast

from pydantic import ValidationError

from quantum.infrastructure.observability.logging.assembler.fallback_builder import (
    FallbackBuilder,
)
from quantum.infrastructure.observability.logging.assembler.payload_assembler import (
    PayloadAssembler,
)
from quantum.infrastructure.observability.logging.core.diagnostics import (
    get_diagnostic_logger,
)
from quantum.infrastructure.observability.logging.core.metrics import define_counter
from quantum.infrastructure.observability.logging.core.trace_context import (
    extract_trace_context,
)
from quantum.infrastructure.observability.logging.exception_processor import (
    ExceptionProcessor,
)
from quantum.infrastructure.observability.logging.models.log_payload_v1 import (
    LogPayloadV1,
)
from quantum.infrastructure.time.format_utils import now_mono_ms, to_rfc3339_ms

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
_SCHEMA_VALIDATION_ERRORS = define_counter("schema_validation_errors")
_diag_logger = get_diagnostic_logger()


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
        trace_id, span_id, is_sampled = extract_trace_context()

        ts_unix_ms = int(record.created * 1000)
        ts_mono_ms = getattr(record, "ts_monotonic_ms", now_mono_ms())

        attrs = self._extract_attrs(record)
        exception_fields = ExceptionProcessor.extract(record)

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
            "correlation_id": getattr(record, "correlation_id", None),
            "run_id": getattr(record, "run_id", None),
            "attrs": attrs,
            **exception_fields,
        }

        try:
            model: LogPayloadV1 = PayloadAssembler.build(record, self._instance_id)
            return model.to_clean_json()

        except ValidationError as e:
            _SCHEMA_VALIDATION_ERRORS.inc()
            _diag_logger.error(
                f"LogPayloadV1 validation failed: {e.__class__.__name__}",
            )

            return FallbackBuilder.build(record, overrides, e)

    # --------------------------------------------------------------------------
    # Internal Helpers
    # --------------------------------------------------------------------------
    def _extract_attrs(self, record: logging.LogRecord) -> dict[str, Any]:
        """Extract and sanitize custom attributes from a LogRecord."""
        attrs: dict[str, Any] = {}

        for k, v in self._filter_record_fields(record).items():
            self._normalize_field(k, v, attrs)

        return cast(dict[str, Any], _json_sanitize(attrs))

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
