from __future__ import annotations

import logging

from pydantic import ValidationError

from quantum.infrastructure.observability.logging.adapters.log_record_adapter import (
    LogRecordAdapter,
)
from quantum.infrastructure.observability.logging.core.metrics import define_counter
from quantum.infrastructure.observability.logging.models.factory import (
    LogPayloadFactory,
)

_SCHEMA_VALIDATION_ERRORS = define_counter("schema_validation_errors")


class PayloadAssembler:
    """
    High-level orchestrator responsible for assembling a validated LogPayload model.

    Responsibilities:
      - Convert LogRecord → InternalLogEvent via LogRecordAdapter
      - Bind DTO → LogPayloadV1 via LogPayloadFactory
      - Count schema validation failures
      - NEVER contain business logic (pure orchestration)
    """

    @staticmethod
    def build(record: logging.LogRecord, instance_id: str):
        """
        Construct a fully validated LogPayloadV1 model.
        May raise ValidationError. Does NOT swallow domain errors.
        """

        # Extract domain-adjacent DTO (safe extraction)
        internal_event = LogRecordAdapter.to_internal_event(
            record=record,
            instance_id=instance_id,
        )

        # Convert DTO → validated domain model
        try:
            payload = LogPayloadFactory.from_internal_event(internal_event)
            return payload

        except ValidationError:
            # Domain model validation failures must be observable
            _SCHEMA_VALIDATION_ERRORS.inc()
            raise
