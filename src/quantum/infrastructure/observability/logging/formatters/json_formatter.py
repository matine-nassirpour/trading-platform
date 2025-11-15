import logging

from pydantic import ValidationError

from quantum.infrastructure.observability.logging.assembler.fallback_builder import (
    FallbackBuilder,
)
from quantum.infrastructure.observability.logging.assembler.override_builder import (
    OverrideBuilder,
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
    Structured JSON formatter.

    Main workflow:
        1. Build model via PayloadAssembler (trusted builder)
        2. Call model.to_clean_json()
        3. If any validation failure → fallback JSON via FallbackBuilder
    """

    def __init__(self, instance_id: str) -> None:
        super().__init__()
        self._instance_id = instance_id

    def format(self, record: logging.LogRecord) -> str:
        """
        Format the record into structured JSON.

        Under normal conditions:
            - assembler produces a validated LogPayload model
            - the model emits clean JSON

        On ValidationError:
            - diagnostic log
            - fallback JSON payload (fail-safe)
        """
        try:
            model = PayloadAssembler.build(record, self._instance_id)
            return model.to_clean_json()

        except ValidationError as e:
            _diag_logger.error(
                f"[formatter] LogPayloadV1 validation failed: {e.__class__.__name__}",
            )
            overrides = OverrideBuilder.build(
                record=record,
                instance_id=self._instance_id,
                trace_id=getattr(record, "trace_id", None),
                span_id=getattr(record, "span_id", None),
                sampled=getattr(record, "sampled", None),
            )
            return FallbackBuilder.build(record, overrides, e)

        except Exception as exc:
            # Any non-schema error must still degrade safely
            _diag_logger.error(
                f"[formatter] unexpected error in JsonFormatter: {exc.__class__.__name__}"
            )
            overrides = OverrideBuilder.build(
                record=record,
                instance_id=self._instance_id,
                trace_id=getattr(record, "trace_id", None),
                span_id=getattr(record, "span_id", None),
                sampled=getattr(record, "sampled", None),
            )
            return FallbackBuilder.build(record, overrides, exc)
