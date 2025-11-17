from __future__ import annotations

import logging

from collections.abc import Iterable
from typing import Final

from quantum.infrastructure.observability.logging.pipeline.engine.base import (
    PipelineStep,
)

_DEFAULT_PREFIXES: Final[set[str]] = {
    "urllib3.connectionpool",
    "requests.packages.urllib3.connectionpool",
    "opentelemetry.sdk._logs",
    "opentelemetry.sdk.trace",
    "opentelemetry.sdk.trace.export",
    "opentelemetry.sdk._shared_internal",
}


class IgnoreLibrariesStep(PipelineStep):
    """Filters out log records from noisy third-party libraries."""

    def __init__(self, noisy_prefixes: Iterable[str] | None = None) -> None:
        self._prefixes = set(noisy_prefixes) if noisy_prefixes else _DEFAULT_PREFIXES

    def process(self, record: logging.LogRecord) -> bool:
        name = getattr(record, "name", "")
        return not any(name.startswith(prefix) for prefix in self._prefixes)
