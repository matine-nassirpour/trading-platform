from __future__ import annotations

import logging

from collections.abc import Mapping
from typing import Any, Final

from quantum.infrastructure.observability.logging.ingestion.log_record_adapter import (
    LogRecordAdapter,
)
from quantum.infrastructure.observability.logging.runtime.metrics import define_counter
from quantum.infrastructure.observability.logging.schemas.fallback.v1.payload import (
    FallbackPayloadV1,
)
from quantum.infrastructure.observability.logging.schemas.log.v1.contract import (
    LogEventContractV1,
)
from quantum.infrastructure.observability.logging.schemas.log.v1.mapping import (
    map_dto_to_contract,
)
from quantum.infrastructure.observability.logging.utils.json_sanitize import (
    json_sanitize,
)

_FALLBACK_BUILDER_FAILURES: Final = define_counter("logging_fallback_builder_failures")
_FALLBACK_MAPPING_ERRORS: Final = define_counter("logging_fallback_mapping_errors")


class FallbackBuilder:
    """
    Industry-grade fallback builder.

    Responsibilities:
        - MUST NEVER RAISE
        - Degrade gracefully under any failure
        - Reconstruct a minimal structured log payload
        - Ensure valid JSON (fallback schema V1)
        - Preserve as much signal as possible (timestamps, message, severity)
        - Always deterministic
    """

    @staticmethod
    def build(
        record: logging.LogRecord,
        instance_id: str,
        error: Exception,
    ) -> FallbackPayloadV1:
        """
        Attempt to produce a structured fallback payload.

        MUST NEVER raise.
        """

        # ----------------------------------------------------------------------
        # Try to extract the DTO (adapter never raises, but defensive)
        # ----------------------------------------------------------------------
        try:
            dto = LogRecordAdapter.to_internal_event(record, instance_id)
        except Exception:
            _FALLBACK_BUILDER_FAILURES.inc()
            return FallbackPayloadV1(
                message="fatal: adapter failed in fallback path",
                fallback_reason="adapter_failure",
                validation_error=str(error),
            )

        # ----------------------------------------------------------------------
        # Try to map DTO → Contract V1 (pure mapping)
        # ----------------------------------------------------------------------
        try:
            contract: LogEventContractV1 = map_dto_to_contract(dto)
        except Exception:
            _FALLBACK_MAPPING_ERRORS.inc()
            return FallbackBuilder._fallback_from_dto(dto, error)

        # ----------------------------------------------------------------------
        # Convert Contract V1 → FallbackPayloadV1
        # ----------------------------------------------------------------------
        try:
            return FallbackBuilder._fallback_from_contract(contract, error)
        except Exception:
            _FALLBACK_BUILDER_FAILURES.inc()
            return FallbackBuilder._fallback_from_dto(dto, error)

    # --------------------------------------------------------------------------
    # INTERNAL HELPERS
    # --------------------------------------------------------------------------
    @staticmethod
    def _fallback_from_contract(
        contract: LogEventContractV1,
        error: Exception,
    ) -> FallbackPayloadV1:
        """
        Convert a valid contract to a safe fallback payload.
        Never raises.
        """

        try:
            attrs: Mapping[str, Any] = contract.attrs
            safe_attrs = json_sanitize(dict(attrs))
        except Exception:
            safe_attrs = {}

        return FallbackPayloadV1(
            # Timestamps
            timestamp=contract.timestamps.timestamp_rfc3339,
            ts_unix_ms=contract.timestamps.ts_unix_ms,
            ts_monotonic_ms=contract.timestamps.ts_monotonic_ms,
            # Severity
            level=contract.severity.level_text,
            severity_number=contract.severity.severity_number,
            # Message
            logger=contract.message.logger_name,
            message=contract.message.message,
            # Resource
            env=contract.resource.env,
            instance=contract.resource.instance_id,
            service_name=contract.resource.service_name,
            service_version=contract.resource.service_version,
            service_namespace=contract.resource.service_namespace,
            # Correlation
            trace_id=contract.correlation.trace_id,
            span_id=contract.correlation.span_id,
            sampled=contract.correlation.sampled,
            correlation_id=contract.correlation.correlation_id,
            run_id=contract.correlation.run_id,
            # Diagnostic
            validation_error=str(error),
            attrs=safe_attrs,
            fallback_reason="model_validation_failure",
        )

    @staticmethod
    def _fallback_from_dto(
        dto,
        error: Exception,
    ) -> FallbackPayloadV1:
        """
        Last-chance fallback using only the DTO.
        Must NEVER raise.
        """

        try:
            safe_attrs = json_sanitize(dict(dto.attrs))
        except Exception:
            safe_attrs = {}

        return FallbackPayloadV1(
            # Timestamps
            timestamp=dto.timestamps.timestamp_rfc3339,
            ts_unix_ms=dto.timestamps.ts_unix_ms,
            ts_monotonic_ms=dto.timestamps.ts_monotonic_ms,
            # Severity
            level=dto.severity.level_text,
            severity_number=dto.severity.severity_number,
            # Message
            logger=dto.message.logger_name,
            message=dto.message.message,
            # Resource
            env=dto.resource.env,
            instance=dto.resource.instance_id,
            service_name=dto.resource.service_name,
            service_version=dto.resource.service_version,
            service_namespace=dto.resource.service_namespace,
            # Correlation
            trace_id=dto.correlation.trace_id,
            span_id=dto.correlation.span_id,
            sampled=dto.correlation.sampled,
            correlation_id=dto.correlation.correlation_id,
            run_id=dto.correlation.run_id,
            # Diagnostic
            validation_error=str(error),
            attrs=safe_attrs,
            fallback_reason="contract_mapping_failure",
        )
