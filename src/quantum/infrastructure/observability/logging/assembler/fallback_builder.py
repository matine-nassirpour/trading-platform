from __future__ import annotations

import logging

from typing import Final

from quantum.infrastructure.observability.logging.adapters.log_record_adapter import (
    LogRecordAdapter,
)
from quantum.infrastructure.observability.logging.core.metrics import define_counter
from quantum.infrastructure.observability.logging.models.fallback_payload_v1 import (
    FallbackPayloadV1,
)
from quantum.infrastructure.observability.logging.utils.json_sanitize import (
    json_sanitize,
)

_FALLBACK_BUILDER_FAILURES: Final = define_counter("logging_fallback_builder_failures")


class FallbackBuilder:
    """
    Contractual fallback builder.

    Responsibilities:
      - NEVER raise
      - Build a valid structured fallback (FallbackPayloadV1)
      - Use LogRecordAdapter (infra) only to extract minimal info
      - Degrade gracefully in worst-case scenarios
    """

    @staticmethod
    def build(
        record: logging.LogRecord,
        instance_id: str,
        error: Exception,
    ) -> FallbackPayloadV1:
        """
        Produce a fully structured fallback payload.
        Must NEVER throw.
        """
        try:
            # Extract whatever is safely extractable using the adapter
            event = LogRecordAdapter.to_internal_event(record, instance_id)

            return FallbackPayloadV1(
                # timestamps
                timestamp=event.timestamp_rfc3339,
                ts_unix_ms=event.ts_unix_ms,
                ts_monotonic_ms=event.ts_monotonic_ms,
                # severity
                level=event.level_text,
                severity_number=event.severity_number,
                # logger + message
                logger=event.logger_name,
                message=event.message,
                # environment
                env=event.env,
                instance=event.instance_id,
                service_name=event.service_name,
                service_version=event.service_version,
                service_namespace=event.service_namespace,
                # correlation
                trace_id=event.trace_id,
                span_id=event.span_id,
                sampled=event.sampled,
                correlation_id=event.correlation_id,
                run_id=event.run_id,
                # diagnostic info
                validation_error=str(error),
                attrs=json_sanitize(dict(event.attrs)),
                fallback_reason="model_validation_failure",
            )

        except Exception:
            # Ultimate fallback — always valid, minimal JSON.
            _FALLBACK_BUILDER_FAILURES.inc()

            return FallbackPayloadV1(
                message="logging failure inside FallbackBuilder",
                fallback_reason="ultimate_fallback",
            )
