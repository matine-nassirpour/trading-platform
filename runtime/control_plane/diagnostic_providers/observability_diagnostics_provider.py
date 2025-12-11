from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from runtime.control_plane.diagnostic_providers.time_provider_dependency import (
    TimeProviderDependency,
)

from quantum.infrastructure.observability.context.context_attributes_provider import (
    ContextAttributesProvider,
)
from quantum.infrastructure.observability.runtime.observability_api import (
    get_diagnostics,
    get_health_registry,
)


@dataclass(frozen=True)
class ObservabilitySnapshot:
    """
    Immutable snapshot of the entire Observability health state.
    Safe for serialization and external system exposure.
    """

    timestamp_utc: str
    pipeline_up: bool
    logging_ok: bool
    logging_sink_up: bool
    tracing_ok: bool
    tracing_up: bool
    metrics_http_ok: bool
    run_id: str | None
    correlation_id: str | None
    diagnostics: dict[str, Any]


class ObservabilityDiagnosticProvider:
    """
    Pure diagnostic provider with NO dependency on web frameworks.

    Responsibilities:
    - Produce a full diagnostic snapshot of Observability internals
    - Query health registry canonical state
    - Include bootstrap diagnostics (latency + failures)
    - Include runtime context (run_id, correlation_id)
    - NEVER raise
    """

    # --------------------------------------------------------------------------
    # Internal helpers
    # --------------------------------------------------------------------------
    @staticmethod
    def _safe_get_diags() -> dict[str, Any]:
        """
        Attempt to retrieve bootstrap diagnostics.
        Always safe, never propagates exceptions.
        """
        try:
            diag = get_diagnostics()
            if diag is None:
                return {"error": "diagnostics_not_installed"}

            return diag.get_summary_report()
        except Exception as exc:
            return {"error": f"diagnostics_unavailable: {exc.__class__.__name__}"}

    # --------------------------------------------------------------------------
    # Public API
    # --------------------------------------------------------------------------
    @staticmethod
    def get_diagnostics_snapshot() -> ObservabilitySnapshot | None:
        """
        Produce a complete diagnostics snapshot.
        Returns None if Observability was never initialized.
        NEVER raises.
        """

        try:
            health = get_health_registry()
        except Exception:
            # Observability not initialized
            return None

        time_provider = TimeProviderDependency.get()
        ctx = ContextAttributesProvider.get()

        diagnostics_summary = ObservabilityDiagnosticProvider._safe_get_diags()

        return ObservabilitySnapshot(
            timestamp_utc=time_provider.now_utc().isoformat(),
            pipeline_up=health.is_pipeline_up(),
            logging_ok=health.is_logging_ok(),
            logging_sink_up=health.is_logging_sink_up(),
            tracing_ok=health.is_tracing_ok(),
            tracing_up=health.is_tracing_up(),
            metrics_http_ok=health.is_metrics_http_ok(),
            run_id=ctx.run_id,
            correlation_id=ctx.correlation_id,
            diagnostics=diagnostics_summary,
        )

    @staticmethod
    def diagnostics_as_dict() -> dict[str, Any] | None:
        snap = ObservabilityDiagnosticProvider.get_diagnostics_snapshot()
        if snap is None:
            return None
        return asdict(snap)
