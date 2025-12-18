from collections.abc import Iterable
from enum import Enum

from contracts.core.base import ContractModel
from contracts.core.versioning import ContractVersion

from .config_diagnostics import ConfigDiagnosticsResponse, ConfigReadyStateSnapshot
from .health import HealthResponse, HealthStatus
from .observability_diagnostics import ObservabilityDiagnosticsResponse
from .runtime_metadata import (
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
