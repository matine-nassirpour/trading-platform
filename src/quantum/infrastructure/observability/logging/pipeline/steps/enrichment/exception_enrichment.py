from __future__ import annotations

import logging

from typing import Any

from quantum.infrastructure.observability.logging.pipeline.engine.step import (
    PipelineStep,
)
from quantum.infrastructure.observability.logging.runtime.exception_processor import (
    ExceptionProcessor,
)


class ExceptionEnrichmentStep(PipelineStep):
    """
    Inject normalized exception fields into record.attrs.
    """

    def process(self, record: logging.LogRecord) -> bool:
        structured_exc: dict[str, Any] = ExceptionProcessor.extract(record)

        if structured_exc:
            base = getattr(record, "attrs", None)

            if isinstance(base, dict):
                merged = base
            else:
                merged = {}

            merged.update(structured_exc)
            record.attrs = merged

        return True
