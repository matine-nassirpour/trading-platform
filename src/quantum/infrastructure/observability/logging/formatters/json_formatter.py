from __future__ import annotations

import logging

from pydantic import ValidationError

from quantum.infrastructure.observability.logging.assembler.fallback_builder import (
    FallbackBuilder,
)
from quantum.infrastructure.observability.logging.assembler.payload_assembler import (
    PayloadAssembler,
)
from quantum.infrastructure.observability.logging.core.diagnostics import (
    get_diagnostic_logger,
)

_diag_logger = get_diagnostic_logger()


class JsonFormatter(logging.Formatter):
    """
    Production-grade structured JSON formatter.

    Responsibilities:
      - Orchestrate the structured logging pipeline
      - Convert LogRecord into domain LogPayloadV1
      - Serialize via to_clean_json()
      - On failure: delegate to FallbackBuilder (structured fallback)
      - Never perform sanitation, overrides, or domain logic
    """

    def __init__(self, instance_id: str) -> None:
        super().__init__()
        self._instance_id = instance_id

    def format(self, record: logging.LogRecord) -> str:
        """
        Main formatting entrypoint:
            LogRecord → InternalEvent → LogPayloadV1 → JSON
        On validation failure:
            → FallbackPayloadV1 → JSON
        """
        try:
            payload = PayloadAssembler.build(record, self._instance_id)
            return payload.to_clean_json()

        except ValidationError as e:
            _diag_logger.error(
                f"[formatter] LogPayloadV1 validation failed: {e.__class__.__name__}"
            )
            fb = FallbackBuilder.build(
                record=record,
                instance_id=self._instance_id,
                error=e,
            )
            return fb.to_json()

        except Exception as exc:
            # Any unexpected error must degrade safely
            _diag_logger.error(
                f"[formatter] unexpected error in JsonFormatter: {exc.__class__.__name__}"
            )
            fb = FallbackBuilder.build(
                record=record,
                instance_id=self._instance_id,
                error=exc,
            )
            return fb.to_json()
