from __future__ import annotations

import logging

from collections.abc import Mapping
from contextlib import suppress
from typing import Any, Final

from quantum.infrastructure.observability.logging.pipeline.engine.step import (
    PipelineStep,
)
from quantum.infrastructure.observability.logging.utils.json_sanitize import (
    json_sanitize,
)

_EXCLUDED_STD_FIELDS: Final[set[str]] = {
    "args",
    "asctime",
    "created",
    "exc_info",
    "exc_text",
    "filename",
    "funcName",
    "levelno",
    "lineno",
    "module",
    "msecs",
    "message",
    "msg",
    "name",
    "pathname",
    "process",
    "processName",
    "relativeCreated",
    "stack_info",
    "thread",
    "threadName",
    "env",
    "service_name",
    "service_version",
    "service_namespace",
    "ts_monotonic_ms",
    "event",
    "correlation_id",
    "run_id",
}


class UnifiedAttrsStep(PipelineStep):
    """
    Unified attribute extractor + normalizer + sanitizer.

    Responsibilities:
        - Extract non-standard fields from LogRecord.__dict__
        - Merge with user-provided record.attrs
        - Normalize structure (always a plain dict)
        - Sanitize JSON recursively (removes non-serializable, exotic types)
        - Never raise under any circumstances
        - Never mutate fields outside record.attrs
    """

    __slots__ = ()

    def process(self, record: logging.LogRecord) -> bool:
        try:
            # ------------------------------------------------------------------
            # Raw extraction of non-standard fields
            # ------------------------------------------------------------------
            raw_attrs: dict[str, Any] = {
                k: v
                for k, v in record.__dict__.items()
                if k not in _EXCLUDED_STD_FIELDS
            }

            exc_val = record.__dict__.get("exception")
            if exc_val is not None:
                with suppress(Exception):
                    if isinstance(exc_val, dict):
                        raw_attrs["exception_obj"] = exc_val
                    else:
                        raw_attrs["exception_text"] = str(exc_val)

            # ------------------------------------------------------------------
            # Retrieving existing attrs
            # ------------------------------------------------------------------
            base_attrs = getattr(record, "attrs", None)

            if isinstance(base_attrs, Mapping):
                merged = dict(base_attrs)  # defensive copy
            elif base_attrs is None:
                merged = {}
            else:
                # Rare edge case: attrs is not a mapping
                merged = {"value": str(base_attrs)}

            # ------------------------------------------------------------------
            # Controlled merger: existing attrs take priority
            # ------------------------------------------------------------------
            for k, v in raw_attrs.items():
                if k not in merged:
                    merged[k] = v

            # ------------------------------------------------------------------
            # Recursive JSON sanitization
            # ------------------------------------------------------------------
            merged = json_sanitize(merged)

            record.attrs = merged
            return True

        except Exception:
            # The pipeline should NEVER be interrupted
            record.attrs = {}
            return True
