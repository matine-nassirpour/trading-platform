from __future__ import annotations

import logging

from collections.abc import Mapping

from quantum.infrastructure.observability.logging.pipeline.engine.step import (
    PipelineStep,
)


class AttrsMergeStep(PipelineStep):
    """Normalizes and merges record.attrs securely."""

    def process(self, record: logging.LogRecord) -> bool:
        attrs = getattr(record, "attrs", None)

        if attrs is None:
            record.attrs = {}
        elif isinstance(attrs, Mapping):
            record.attrs = dict(attrs)
        else:
            record.attrs = {"value": str(attrs)}

        return True
