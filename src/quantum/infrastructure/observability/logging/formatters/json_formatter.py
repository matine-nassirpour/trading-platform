from __future__ import annotations

import logging

from pydantic import ValidationError

from quantum.infrastructure.observability.logging.assembly.fallback_builder import (
    FallbackBuilder,
)
from quantum.infrastructure.observability.logging.assembly.payload_assembler import (
    PayloadAssembler,
)
from quantum.infrastructure.observability.logging.runtime.diagnostics import (
    get_diagnostic_logger,
)

_diag_logger = get_diagnostic_logger()


class JsonFormatter(logging.Formatter):
    """
    Responsibilities:
    - Coordinate the high-level structured logging pipeline:
        LogRecord → DTO → Contract → Domain Payload → JSON
    - Apply no enrichment and no sanitation (all upstream)
    - Convert failures to structured fallback payloads
    - NEVER raise under any circumstance
    """

    def __init__(self, instance_id: str) -> None:
        super().__init__()
        self._instance_id = instance_id

    def format(self, record: logging.LogRecord) -> str:
        """
        High-level pipeline:
            1. PayloadAssembler.build()  -> validated domain payload
            2. Payload.to_clean_json()
        On failure:
            -> FallbackBuilder.build()  -> fallback JSON

        This method must NEVER raise.
        """

        try:
            payload = PayloadAssembler.build(record, self._instance_id)
            return payload.to_clean_json()

        except ValidationError as exc:
            _diag_logger.error(
                f"[formatter] payload validation failed: {exc.__class__.__name__}"
            )
            fb = FallbackBuilder.build(
                record=record,
                instance_id=self._instance_id,
                error=exc,
            )
            return fb.to_json()

        except Exception as exc:
            _diag_logger.error(
                f"[formatter] unexpected error: {exc.__class__.__name__}"
            )
            fb = FallbackBuilder.build(
                record=record,
                instance_id=self._instance_id,
                error=exc,
            )
            return fb.to_json()
