from __future__ import annotations

import logging

from typing import Final

from pydantic import ValidationError

from quantum.infrastructure.observability.logging.core.mapping.to_contract import (
    map_dto_to_contract,
)
from quantum.infrastructure.observability.logging.core.mapping.to_payload import (
    map_contract_to_payload,
)
from quantum.infrastructure.observability.logging.core.models.log_payload import (
    LogPayload,
)
from quantum.infrastructure.observability.logging.ingestion.log_record_adapter import (
    LogRecordAdapter,
)
from quantum.infrastructure.observability.logging.runtime.diagnostics import (
    get_diagnostic_logger,
)
from quantum.infrastructure.observability.logging.runtime.metrics import define_counter

# Counts schema validation failures (Pydantic)
_SCHEMA_VALIDATION_ERRORS: Final = define_counter("schema_validation_errors")

# Counts failures in the mapping pipeline (unexpected errors)
_ASSEMBLER_UNEXPECTED_ERRORS: Final = define_counter("assembler_unexpected_errors")

# Fail-safe logger (C0), entirely independent of user logging config
_diag_logger = get_diagnostic_logger()


class PayloadAssembler:
    """
    High-level orchestrator responsible for producing a validated LogPayload model.

    Responsibilities:
        - Act as a *pure* orchestration layer (SRP).
        - Convert LogRecord → InternalLogEvent (via LogRecordAdapter).
        - Convert InternalLogEvent → LogEventContractV1 (strict domain contract).
        - Convert LogEventContractV1 → LogPayload (Pydantic validation).
        - Count validation failures.
        - Never swallow domain ValidationError (caller must handle).
        - Degrade safely and observably on unexpected assembler-level exceptions.
    """

    @staticmethod
    def build(record: logging.LogRecord, instance_id: str) -> LogPayload:
        """Construct a validated LogPayload model from a LogRecord."""

        # ----------------------------------------------------------------------
        # Convert LogRecord → DTO (safe adapter)
        # ----------------------------------------------------------------------
        internal_event = LogRecordAdapter.to_internal_event(
            record=record,
            instance_id=instance_id,
        )

        # ----------------------------------------------------------------------
        # Convert DTO → Contract (explicit & versioned)
        # ----------------------------------------------------------------------
        try:
            contract = map_dto_to_contract(internal_event)
        except Exception as exc:
            # This should almost never fail, but if it does,
            # the system must remain diagnosable.
            _ASSEMBLER_UNEXPECTED_ERRORS.inc()
            _diag_logger.error(
                f"[PayloadAssembler] contract mapping failed ({exc.__class__.__name__})"
            )
            raise

        # ----------------------------------------------------------------------
        # Convert Contract → Domain Payload (strict validation)
        # ----------------------------------------------------------------------
        try:
            payload = map_contract_to_payload(contract)
            return payload

        except ValidationError as exc:
            _SCHEMA_VALIDATION_ERRORS.inc()
            _diag_logger.error(
                f"[PayloadAssembler] payload validation failed: {exc.__class__.__name__}"
            )
            raise

        except Exception as exc:
            _ASSEMBLER_UNEXPECTED_ERRORS.inc()
            _diag_logger.error(
                f"[PayloadAssembler] unexpected error: {exc.__class__.__name__}"
            )
            raise
