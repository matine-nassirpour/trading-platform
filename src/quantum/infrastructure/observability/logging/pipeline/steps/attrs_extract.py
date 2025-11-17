from __future__ import annotations

import logging

from contextlib import suppress
from typing import Any

from quantum.infrastructure.observability.logging.metadata.constants import (
    EXCLUDED_STD_FIELDS,
)
from quantum.infrastructure.observability.logging.pipeline.engine.base import (
    PipelineStep,
)
from quantum.infrastructure.observability.logging.utils.json.json_sanitize import (
    json_sanitize,
)


class AttrsExtractStep(PipelineStep):
    """Extract sanitized attributes from a LogRecord."""

    def process(self, record: logging.LogRecord) -> bool:
        raw = {k: v for k, v in record.__dict__.items() if k not in EXCLUDED_STD_FIELDS}

        attrs: dict[str, Any] = {}

        for key, value in raw.items():

            # Special case: exception object
            if key == "exception":
                with suppress(Exception):
                    if isinstance(value, dict):
                        attrs["exception_obj"] = value
                    elif value is not None:
                        attrs["exception_text"] = str(value)
                continue

            # Merge existing attrs dict
            if key == "attrs" and isinstance(value, dict):
                attrs.update(value)
                continue

            attrs[key] = value

        # Global sanitize
        record.attrs = json_sanitize(attrs)
        return True
