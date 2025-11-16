from __future__ import annotations

import logging

from pydantic import ValidationError

from quantum.infrastructure.observability.logging.assembler.override_builder import (
    OverrideBuilder,
)
from quantum.infrastructure.observability.logging.core.metrics import define_counter
from quantum.infrastructure.observability.logging.core.trace_context import (
    extract_trace_context,
)
from quantum.infrastructure.observability.logging.models.factory import from_log_record

_SCHEMA_VALIDATION_ERRORS = define_counter("schema_validation_errors")


class PayloadAssembler:
    """
    Assemble a validated LogPayload model (LogPayloadV1).
    This class performs *only* assembling and validation, no formatting.

    - Extracts context (trace_id, span_id, sampled)
    - Constructs a fully-populated override dict
    - Hands the construction to `from_log_record` for schema binding
    - On validation failure: increments metric and re-raises ValidationError
    """

    @staticmethod
    def build(record: logging.LogRecord, instance_id: str):
        trace_id, span_id, is_sampled = extract_trace_context()

        overrides = OverrideBuilder.build(
            record=record,
            instance_id=instance_id,
            trace_id=trace_id,
            span_id=span_id,
            sampled=is_sampled,
        )

        # Try constructing and validating the payload model
        try:
            model = from_log_record(record, **overrides)
            return model

        except ValidationError:
            # Count internal schema failures
            _SCHEMA_VALIDATION_ERRORS.inc()
            raise
