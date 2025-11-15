from __future__ import annotations

import logging

from contextlib import suppress
from typing import Any

from quantum.infrastructure.observability.logging.exception_processor import (
    ExceptionProcessor,
)


class ExceptionEnrichmentStep:
    """
    Inject normalized exception fields into record.attrs.
    """

    def apply(self, record: logging.LogRecord) -> None:
        """Safely enrich record.attrs with structured exception representation."""
        with suppress(Exception):
            structured_exc: dict[str, Any] = ExceptionProcessor.extract(record)
            if structured_exc:
                if not hasattr(record, "attrs") or not isinstance(record.attrs, dict):
                    record.attrs = {}
                record.attrs.update(structured_exc)
