from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from runtime.control_plane.diagnostic_providers.time_provider_dependency import (
    TimeProviderDependency,
)

from quantum.infrastructure.observability.bootstrap.runtime_status_provider import (
    ObservabilityRuntimeStatusProvider,
)
from quantum.infrastructure.observability.context.context_attributes_provider import (
    ContextAttributesProvider,
)


@dataclass(frozen=True)
class ObservabilitySnapshot:
    """
    Immutable snapshot of the entire Observability health state.
    This object is serializable and can be safely exposed to external systems.
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
    def _safe_get_diag(diag) -> dict[str, Any]:
        if diag is None:
            return {"error": "bootstrap_diagnostics_not_installed"}

        try:
            return diag.get_summary_report()
        except Exception as exc:
            return {"error": f"diagnostics_unavailable: {exc.__class__.__name__}"}

    # --------------------------------------------------------------------------
    # Public API
    # --------------------------------------------------------------------------
    @staticmethod
    def get_diagnostics() -> ObservabilitySnapshot | None:
        health = ObservabilityRuntimeStatusProvider.get_health_registry()
        diag = ObservabilityRuntimeStatusProvider.get_bootstrap_diagnostics()

        if health is None:
            # Observability not initialized
            return None

        time_provider = TimeProviderDependency.get()
        ctx = ContextAttributesProvider.get()

        diag_summary = ObservabilityDiagnosticProvider._safe_get_diag(diag)

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
            diagnostics=diag_summary,
        )

    @staticmethod
    def diagnostics_as_dict() -> dict[str, Any] | None:
        snap = ObservabilityDiagnosticProvider.get_diagnostics()
        if snap is None:
            return None
        return asdict(snap)
