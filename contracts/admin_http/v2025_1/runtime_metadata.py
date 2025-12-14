from dataclasses import dataclass

from contracts.core.base import ContractModel
from contracts.core.versioning import ContractVersion

VERSION = ContractVersion(2025, 1)


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
    status: str
    api_version: str
    admin_http: AdminHttpDescriptor
