from collections.abc import Iterable
from enum import Enum

from contracts.core.model import ContractModel
from contracts.core.versioning import ContractVersion
from contracts.surfaces.admin_http.v2025_1.config_diagnostics.models import (
    ConfigDiagnosticsResponse,
    ConfigReadyStateSnapshot,
)
from contracts.surfaces.admin_http.v2025_1.health.models import (
    HealthResponse,
    HealthStatus,
)
from contracts.surfaces.admin_http.v2025_1.observability_diagnostics.models import (
    ObservabilityDiagnosticsResponse,
)
from contracts.surfaces.admin_http.v2025_1.runtime_metadata.models import (
    VERSION,
    AdminEndpoints,
    AdminHttpDescriptor,
    ApiVersionDescriptor,
    RuntimeMetadataResponse,
    SystemStatus,
)

CONTRACT_VERSION: ContractVersion = VERSION

ENUMS: Iterable[type[Enum]] = [
    SystemStatus,
    HealthStatus,
]

MODELS: Iterable[type[ContractModel]] = [
    ApiVersionDescriptor,
    AdminEndpoints,
    AdminHttpDescriptor,
    RuntimeMetadataResponse,
    HealthResponse,
    ConfigReadyStateSnapshot,
    ConfigDiagnosticsResponse,
    ObservabilityDiagnosticsResponse,
]
