from dataclasses import dataclass
from enum import Enum

from contracts.core.model import ContractModel
from contracts.core.version.model import ApiVersionDescriptor


class SystemStatus(str, Enum):
    UP = "UP"
    DEGRADED = "DEGRADED"
    DOWN = "DOWN"


@dataclass(frozen=True)
class AdminEndpoints(ContractModel):
    health: str
    runtime_metadata: str
    config_diagnostics: str
    observability_diagnostics: str


@dataclass(frozen=True)
class AdminHttpDescriptor(ContractModel):
    base_url: str
    endpoints: AdminEndpoints


@dataclass(frozen=True)
class RuntimeMetadataResponse(ContractModel):
    status: SystemStatus
    api_version: ApiVersionDescriptor
    admin_http: AdminHttpDescriptor
