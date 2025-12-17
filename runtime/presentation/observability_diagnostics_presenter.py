from typing import Any

from runtime.admin.diagnostics.observability import ObservabilityDiagnosticsSnapshot
from runtime.presentation.safety import safe_expose


class ObservabilityDiagnosticsPresenter:
    """
    Canonical projection from internal runtime diagnostics snapshot
    to an external-facing, contract-compatible representation.
    """

    @staticmethod
    def present(snapshot: ObservabilityDiagnosticsSnapshot) -> dict[str, Any] | None:
        """
        Produce a contract-compatible payload.

        Rules:
        - NEVER raise
        - NEVER expose internal-only structures
        - NEVER mutate snapshot
        - Field mapping is EXPLICIT (no reflection / __dict__)
        """

        if snapshot is None:
            return None

        return {
            "pipeline_up": snapshot.pipeline_up,
            "logging_ok": snapshot.logging_ok,
            "logging_sink_up": snapshot.logging_sink_up,
            "tracing_ok": snapshot.tracing_ok,
            "tracing_up": snapshot.tracing_up,
            "metrics_http_ok": snapshot.metrics_http_ok,
            "run_id": snapshot.run_id,
            "correlation_id": snapshot.correlation_id,
            "diagnostics": safe_expose(snapshot.diagnostics),
        }
