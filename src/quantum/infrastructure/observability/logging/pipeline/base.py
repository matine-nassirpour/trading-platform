from __future__ import annotations

import logging

from abc import ABC, abstractmethod


class PipelineStep(ABC):
    """Strict contract for a pre-processing step of a LogRecord."""

    @abstractmethod
    def process(self, record: logging.LogRecord) -> bool:
        """Apply transformation or filtering. Return False to drop the record."""
        raise NotImplementedError
