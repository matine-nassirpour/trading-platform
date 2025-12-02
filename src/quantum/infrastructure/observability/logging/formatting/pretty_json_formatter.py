from __future__ import annotations

import json
import logging

from quantum.infrastructure.observability.logging.formatting.json_formatter import (
    JsonFormatter,
)


class PrettyJsonFormatter(JsonFormatter):
    """
    Human-facing pretty JSON formatter for console output.

    Guarantees:
    - NEVER raises (even if JSON is malformed)
    - Pretty-indented output (indent=2)
    - Strictly wraps JsonFormatter (no enrichment, no mutation)
    - Only used for console logs (never for machine pipelines)
    """

    def format(self, record: logging.LogRecord) -> str:
        # Step 1 — get strict compact JSON from parent formatter
        raw = super().format(record)

        # Step 2 — pretty-print with graceful fallback
        try:
            obj = json.loads(raw)
            return json.dumps(
                obj,
                ensure_ascii=False,
                indent=2,
                separators=(",", ": "),
            )
        except Exception:
            # fallback: never interrupt logging pipeline
            return raw
