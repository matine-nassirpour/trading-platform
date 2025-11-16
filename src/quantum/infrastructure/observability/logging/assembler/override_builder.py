from __future__ import annotations

import logging

from typing import Any

from quantum.infrastructure.observability.logging.exception_processor import (
    EXCEPTION_FIELD_NAMES,
)
from quantum.infrastructure.observability.logging.utils.json_sanitize import (
    json_sanitize,
)
from quantum.infrastructure.time.format_utils import now_mono_ms, to_rfc3339_ms


class OverrideBuilder:
    """
    Centralized, authoritative builder for all log schema override fields.
    """

    @staticmethod
    def build(
        record: logging.LogRecord,
        *,
        instance_id: str,
        trace_id: str | None,
        span_id: str | None,
        sampled: bool | None,
    ) -> dict[str, Any]:
        """
        Build a complete, sanitized override dictionary aligned with the log schema.
        """

        # ─── Unix timestamp
        try:
            created = getattr(record, "created", 0.0)
            ts_unix_ms = int(created * 1000) if created else 0
        except Exception:
            created = 0.0
            ts_unix_ms = 0

        # ─── Monotonic timestamp
        try:
            ts_mono_ms = getattr(record, "ts_monotonic_ms", None)
            if ts_mono_ms is None:
                ts_mono_ms = now_mono_ms()
            else:
                ts_mono_ms = int(ts_mono_ms)
        except Exception:
            ts_mono_ms = now_mono_ms()

        overrides = {
            # Timestamps (OTel-aligned)
            "timestamp": to_rfc3339_ms(created),
            "ts_unix_ms": ts_unix_ms,
            "ts_monotonic_ms": ts_mono_ms,
            # Environment / resource
            "env": getattr(record, "env", None),
            "instance": instance_id,
            "service_name": getattr(record, "service_name", None),
            "service_version": getattr(record, "service_version", None),
            "service_namespace": getattr(record, "service_namespace", None),
            # Tracing & correlation context
            "trace_id": trace_id,
            "span_id": span_id,
            "sampled": sampled,
            "correlation_id": getattr(record, "correlation_id", None),
            "run_id": getattr(record, "run_id", None),
            # Custom attributes (structured log fields)
            "attrs": json_sanitize(getattr(record, "attrs", {})),
        }

        return {k: v for k, v in overrides.items() if k not in EXCEPTION_FIELD_NAMES}
