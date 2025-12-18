from dataclasses import dataclass
from enum import Enum

from contracts.core.base import ContractModel
from contracts.core.versioning import ContractVersion

VERSION = ContractVersion(2025, 1)


class SystemStatus(str, Enum):
    """
    Contractual external system status.

    This enum is part of the ADMIN HTTP CONTRACT.
    It MUST remain stable across minor revisions.
    """

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
    api_version: str
    admin_http: AdminHttpDescriptor
