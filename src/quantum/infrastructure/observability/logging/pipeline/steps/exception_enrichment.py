from __future__ import annotations

import logging

from typing import Any

from quantum.infrastructure.observability.logging.exception_processor import (
    ExceptionProcessor,
)
from quantum.infrastructure.observability.logging.pipeline.base import PipelineStep


class ExceptionEnrichmentStep(PipelineStep):
    """
    Inject normalized exception fields into record.attrs.
    """

    def process(self, record: logging.LogRecord) -> bool:
        structured_exc: dict[str, Any] = ExceptionProcessor.extract(record)

        if structured_exc:
            attrs = record.attrs if isinstance(record.attrs, dict) else {}
            attrs.update(structured_exc)
            record.attrs = attrs

        return True
