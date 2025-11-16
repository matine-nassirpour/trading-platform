from __future__ import annotations

import logging

from collections.abc import Mapping
from typing import Final

from quantum.infrastructure.observability.logging.core.metrics import define_counter
from quantum.infrastructure.observability.logging.core.trace_context import (
    extract_trace_context,
)
from quantum.infrastructure.observability.logging.dto.internal_log_event import (
    InternalLogEvent,
)
from quantum.infrastructure.observability.logging.exception_processor import (
    ExceptionProcessor,
)
from quantum.infrastructure.observability.logging.models.severity_map import (
    canonical_severity,
)
from quantum.infrastructure.observability.logging.utils.json_sanitize import (
    json_sanitize,
)
from quantum.infrastructure.observability.logging.utils.time_format import (
    now_mono_ms,
    to_rfc3339_ms,
)

_ADAPTER_RECOVERABLE_ERRORS: Final = define_counter(
    "logging_adapter_recoverable_errors"
)


class LogRecordAdapter:
    """
    Adapter responsible for translating a Python LogRecord (infrastructure)
    into a domain-adjacent InternalLogEvent DTO.

    Responsibilities:
      - Safe extraction from LogRecord (never raises)
      - Mapping to canonical severity
      - Timestamps normalization
      - Extraction of tracing context
      - Raw exception extraction (no schema-level normalization)
      - Extraction of structured attributes (attrs)
      - Strict isolation of LogRecord from the rest of the system
    """

    @staticmethod
    def to_internal_event(
        record: logging.LogRecord,
        instance_id: str,
    ) -> InternalLogEvent:
        """
        Convert LogRecord → InternalLogEvent safely and deterministically.
        """

        # ─── timestamps
        created_ts = getattr(record, "created", 0.0)
        ts_unix_ms = int(created_ts * 1000) if created_ts else 0

        try:
            ts_mono_ms = getattr(record, "ts_monotonic_ms", None)
            if ts_mono_ms is None:
                ts_mono_ms = now_mono_ms()
            else:
                ts_mono_ms = int(ts_mono_ms)
        except Exception:
            _ADAPTER_RECOVERABLE_ERRORS.inc()
            ts_mono_ms = now_mono_ms()

        timestamp_rfc3339 = to_rfc3339_ms(created_ts)

        # ─── severity
        levelno = getattr(record, "levelno", logging.INFO)
        level_text, sev_num = canonical_severity(int(levelno))

        # ─── tracing context (global extractor)
        trace_id, span_id, is_sampled = extract_trace_context()

        # ─── raw exception block
        exc_block = ExceptionProcessor.extract(record)

        # ─── attributes
        attrs = getattr(record, "attrs", {})
        if not isinstance(attrs, Mapping):
            _ADAPTER_RECOVERABLE_ERRORS.inc()
            attrs = {}

        # sanitization must not modify original record
        try:
            attrs = json_sanitize(dict(attrs))
        except Exception:
            _ADAPTER_RECOVERABLE_ERRORS.inc()
            attrs = {}

        return InternalLogEvent(
            # timestamps
            timestamp_rfc3339=timestamp_rfc3339,
            ts_unix_ms=ts_unix_ms,
            ts_monotonic_ms=ts_mono_ms,
            # severity
            level_text=level_text,
            severity_number=sev_num,
            # logger metadata
            logger_name=getattr(record, "name", "unknown_logger"),
            message=record.getMessage(),
            # resource info
            env=getattr(record, "env", None),
            instance_id=instance_id,
            service_name=getattr(record, "service_name", None),
            service_version=getattr(record, "service_version", None),
            service_namespace=getattr(record, "service_namespace", None),
            # tracing / correlation
            trace_id=trace_id,
            span_id=span_id,
            sampled=is_sampled,
            correlation_id=getattr(record, "correlation_id", None),
            run_id=getattr(record, "run_id", None),
            # exception block
            exception_type=exc_block.get("exception_type"),
            exception_message=exc_block.get("exception_message"),
            exception_stacktrace=exc_block.get("exception_stacktrace"),
            exception_summary=exc_block.get("exception"),
            # flexible structured attributes
            attrs=attrs,
        )
