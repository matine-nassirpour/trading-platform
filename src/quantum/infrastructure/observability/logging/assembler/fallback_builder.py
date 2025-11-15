import json
import logging

from typing import Any

from quantum.infrastructure.observability.logging.models.severity_map import (
    SEVERITY_MAP,
)
from quantum.infrastructure.observability.logging.utils.json_sanitize import (
    json_sanitize,
)


# ╭────────────────────────────────────────────────────────────────────────────╮
# │ Internal Helpers                                                           │
# ╰────────────────────────────────────────────────────────────────────────────╯
def _safe_record_field(
    record: logging.LogRecord, field: str, default: Any = None
) -> Any:
    """
    Safe extraction from LogRecord without risking attribute errors.
    """
    return json_sanitize(getattr(record, field, default))


# ╭────────────────────────────────────────────────────────────────────────────╮
# │ Fallback Builder                                                           │
# ╰────────────────────────────────────────────────────────────────────────────╯
class FallbackBuilder:
    """
    Fail-safe JSON fallback payload builder.

    This builder must NEVER fail.
    If anything goes wrong, it emits an ultra-minimal JSON payload.
    """

    @staticmethod
    def build(
        record: logging.LogRecord, overrides: dict[str, Any], error: Exception
    ) -> str:
        """
        Build a fully sanitized fallback JSON payload.

        Everything is protected by try/except to guarantee that:
        - No exception can propagate
        - The function always returns valid JSON
        """
        try:
            return FallbackBuilder._build_safe(record, overrides, error)
        except Exception:
            # Absolute fail-safe fallback: a minimal schema that cannot fail
            return json.dumps(
                {
                    "schema": "quantum.log",
                    "log_schema_version": "fallback_minimal",
                    "message": "Logging failure inside fallback builder",
                    "error": "unrecoverable_fallback_failure",
                },
                ensure_ascii=False,
                separators=(",", ":"),
            )

    @staticmethod
    def _build_safe(
        record: logging.LogRecord,
        overrides: dict[str, Any],
        error: Exception,
    ) -> str:
        sev_text, sev_num = FallbackBuilder._safe_severity(record)

        payload = {
            "schema": "quantum.log",
            "log_schema_version": "fallback",
            # timestamps
            "timestamp": overrides.get("timestamp"),
            "ts_unix_ms": overrides.get("ts_unix_ms"),
            "ts_monotonic_ms": overrides.get("ts_monotonic_ms"),
            # core severity
            "level": sev_text,
            "severity_number": sev_num,
            # logger info
            "logger": _safe_record_field(record, "name", "unknown_logger"),
            "message": _safe_record_field(record, "msg", None),
            # service context
            "env": overrides.get("env"),
            "instance": overrides.get("instance"),
            "service_name": overrides.get("service_name"),
            "service_version": overrides.get("service_version"),
            "service_namespace": overrides.get("service_namespace"),
            # correlation & tracing
            "trace_id": overrides.get("trace_id"),
            "span_id": overrides.get("span_id"),
            "sampled": overrides.get("sampled"),
            "correlation_id": overrides.get("correlation_id"),
            "run_id": overrides.get("run_id"),
            # diagnostic info
            "validation_error": json_sanitize(str(error)),
            "attrs": overrides.get("attrs", {}),
            # static safety marker
            "fallback_reason": "schema_validation_failure",
        }

        # Final safe JSON encoding
        return json.dumps(
            payload,
            ensure_ascii=False,
            separators=(",", ":"),
        )

    @staticmethod
    def _safe_severity(record: logging.LogRecord) -> tuple[str, int]:
        """
        Safe resolution of severity text/number.
        Always returns a valid pair.
        """
        try:
            level = int(getattr(record, "levelno", logging.INFO))
        except Exception:
            level = logging.INFO

        return SEVERITY_MAP.get(level, ("INFO", 9))
