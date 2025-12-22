from __future__ import annotations

from enum import Enum
from typing import Final

from contracts.core.model import ContractModel
from contracts.core.version.model import ApiVersionDescriptor
from contracts.core.version.versioning import ContractVersion
from contracts.surfaces.control_plane_http.v2025_1.config_diagnostics.models import (
    ConfigDiagnosticsResponse,
    ConfigReadyStateSnapshot,
)
from contracts.surfaces.control_plane_http.v2025_1.health.models import (
    HealthResponse,
    HealthStatus,
)
from contracts.surfaces.control_plane_http.v2025_1.observability_diagnostics.models import (
    ObservabilityDiagnosticsResponse,
)
from contracts.surfaces.control_plane_http.v2025_1.runtime_metadata.models import (
    AdminEndpoints,
    AdminHttpDescriptor,
    RuntimeMetadataResponse,
    SystemStatus,
)

SURFACE_NAME: Final[str] = "control_plane_http"

CONTRACT_VERSION: Final[ContractVersion] = ContractVersion(
    year=2025,
    revision=1,
)

ENUMS: Final[tuple[type[Enum], ...]] = (
    SystemStatus,
    HealthStatus,
)

MODELS: Final[tuple[type[ContractModel], ...]] = (
    ApiVersionDescriptor,
    AdminEndpoints,
    AdminHttpDescriptor,
    RuntimeMetadataResponse,
    HealthResponse,
    ConfigReadyStateSnapshot,
    ConfigDiagnosticsResponse,
    ObservabilityDiagnosticsResponse,
)


def _validate_manifest() -> None:
    # Enums must be string-based
    for enum in ENUMS:
        for member in enum:
            if not isinstance(member.value, str):
                raise TypeError(
                    f"Contract enum {enum.__name__} must use string values only"
                )

    # Models must be ContractModel subclasses
    for model in MODELS:
        if not issubclass(model, ContractModel):
            raise TypeError(f"Invalid model in manifest: {model!r}")

    # Deterministic ordering guarantee
    if len(set(ENUMS)) != len(ENUMS):
        raise ValueError("Duplicate enum detected in ENUMS")

    if len(set(MODELS)) != len(MODELS):
        raise ValueError("Duplicate model detected in MODELS")


_validate_manifest()
