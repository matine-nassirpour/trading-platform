from __future__ import annotations

from contracts.core.version.model import ApiVersionDescriptor
from contracts.core.version.versioning import ContractVersion


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
    """
    if not isinstance(descriptor, ApiVersionDescriptor):
        raise TypeError("descriptor must be an ApiVersionDescriptor")

    return ContractVersion(
        year=descriptor.year,
        revision=descriptor.revision,
    )
