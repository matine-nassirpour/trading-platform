import json
import logging

from typing import Any

from quantum.infrastructure.observability.logging.models.severity_map import (
    SEVERITY_MAP,
)


class FallbackBuilder:
    """Construct a stripped-down JSON fallback payload."""

    @staticmethod
    def build(
        record: logging.LogRecord, overrides: dict[str, Any], error: Exception
    ) -> str:
        sev_text, sev_num = SEVERITY_MAP.get(record.levelno, ("INFO", 9))

        payload = {
            "timestamp": overrides["timestamp"],
            "ts_unix_ms": overrides["ts_unix_ms"],
            "ts_monotonic_ms": overrides["ts_monotonic_ms"],
            "level": sev_text,
            "severity_number": sev_num,
            "logger": record.name,
            "message": record.getMessage(),
            "env": overrides["env"],
            "instance": overrides["instance"],
            "service_name": overrides["service_name"],
            "service_version": overrides["service_version"],
            "service_namespace": overrides["service_namespace"],
            "trace_id": overrides["trace_id"],
            "span_id": overrides["span_id"],
            "sampled": overrides["sampled"],
            "correlation_id": overrides["correlation_id"],
            "run_id": overrides["run_id"],
            "schema": "quantum.log",
            "log_schema_version": "fallback",
            "validation_error": str(error),
            "attrs": overrides["attrs"],
        }

        return json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
