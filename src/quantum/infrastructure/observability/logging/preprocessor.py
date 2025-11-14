from __future__ import annotations

import logging
import time

from collections.abc import Mapping

from quantum.infrastructure.observability.context.run_id import get_run_id
from quantum.infrastructure.observability.tracing.correlation.correlation_id import (
    get_correlation_id,
)

from .filters.ignore_libraries_filter import IgnoreLibrariesFilter
from .filters.redact_filter import RedactFilter


class RecordPreprocessor(logging.Filter):
    """
    Central preprocessor for all log records.
    This consolidates ALL enrichment and normalization steps
    into a single, deterministic, testable component.

    Responsibilities:
        - add environment metadata
        - inject timestamps
        - inject correlation and run_id
        - merge attrs
        - apply redaction
        - remove noisy libraries
    """

    def __init__(
        self,
        *,
        env: str,
        namespace: str,
        app_name: str,
        version: str,
    ) -> None:
        super().__init__()
        self.env = env
        self.namespace = namespace
        self.app_name = app_name
        self.version = version

        self._redactor = RedactFilter()
        self._ignore = IgnoreLibrariesFilter()

    def filter(self, record: logging.LogRecord) -> bool:
        """
        Apply all preprocessing to the record in place.
        Returns False if the record should be dropped.
        """

        # 1. Drop noisy libraries
        if not self._ignore.filter(record):
            return False

        # 2. Inject timestamps
        if not hasattr(record, "ts_monotonic_ms"):
            record.ts_monotonic_ms = time.monotonic_ns() // 1_000_000

        # 3. Merge attrs (safer than record.extra)
        attrs = getattr(record, "attrs", None)
        if attrs is None:
            attrs = {}
        elif not isinstance(attrs, Mapping):
            attrs = {"value": str(attrs)}
        record.attrs = dict(attrs)

        # 4. Inject resource attributes
        record.env = getattr(record, "env", self.env)
        record.service_name = getattr(record, "service_name", self.app_name)
        record.service_version = getattr(record, "service_version", self.version)
        record.service_namespace = getattr(record, "service_namespace", self.namespace)

        # 5. Inject global correlation
        record.correlation_id = getattr(record, "correlation_id", get_correlation_id())
        record.run_id = getattr(record, "run_id", get_run_id())

        # 6. Apply redaction
        self._redactor.filter(record)

        return True
