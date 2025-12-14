from dataclasses import dataclass
from typing import Any

from contracts.core.base import ContractModel


@dataclass(frozen=True)
class ObservabilityDiagnosticsResponse(ContractModel):
    pipeline_up: bool
    logging_ok: bool
    logging_sink_up: bool
    tracing_ok: bool
    tracing_up: bool
    metrics_http_ok: bool
    run_id: str | None
    correlation_id: str | None
    diagnostics: dict[str, Any]
