from __future__ import annotations

from contracts.core.version.versioning import ContractVersion
from contracts.surfaces.admin_http.v2025_1.runtime_metadata.models import (
    ApiVersionDescriptor,
)


def contract_version_to_api_descriptor(
    version: ContractVersion,
) -> ApiVersionDescriptor:
    """
    Project an internal ContractVersion to a wire-level ApiVersionDescriptor.
    """
    if not isinstance(version, ContractVersion):
        raise TypeError("version must be a ContractVersion")

    return ApiVersionDescriptor(
        year=version.year,
        revision=version.revision,
    )


def api_descriptor_to_contract_version(
    descriptor: ApiVersionDescriptor,
) -> ContractVersion:
    """
    Convert a wire-level ApiVersionDescriptor back to a ContractVersion.
    This function exists mainly for validation, tooling and tests.
    """
    if not isinstance(descriptor, ApiVersionDescriptor):
        raise TypeError("descriptor must be an ApiVersionDescriptor")

    return ContractVersion(
        year=descriptor.year,
        revision=descriptor.revision,
    )
