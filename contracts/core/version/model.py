from dataclasses import dataclass

from contracts.core.model import ContractModel
from contracts.core.validation import ContractViolation
from contracts.core.version.versioning import ContractVersion


@dataclass(frozen=True)
class ApiVersionDescriptor(ContractModel):
    """
    Wire-level, contract-stable projection of ContractVersion.

    This DTO is:
    - external-facing
    - serialization-safe
    - versioned with the API surface

    It is NOT a source of truth.
    """

    year: int
    revision: int

    def __post_init__(self) -> None:
        # Run base contract validation
        super().__post_init__()

        # Enforce consistency with ContractVersion invariants
        try:
            ContractVersion(year=self.year, revision=self.revision)
        except Exception as exc:
            raise ContractViolation(f"Invalid ApiVersionDescriptor: {exc}") from exc
