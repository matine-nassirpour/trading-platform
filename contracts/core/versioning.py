from dataclasses import dataclass


@dataclass(frozen=True, order=True)
class ContractVersion:
    """
    Immutable contract release identifier.

    Versioning model: CALVER (Calendar Versioning)

    Semantics:
    - year     : calendar year of the contract release
    - revision : monotonically increasing, per-year

    Rules:
    - A backward-incompatible change REQUIRES a new ContractVersion
    - Published contract versions are IMMUTABLE
    - A version uniquely identifies a contract surface
    """

    year: int
    revision: int

    def __post_init__(self) -> None:
        if self.year < 2025:
            raise ValueError("ContractVersion.year must be >= 2025")
        if self.revision < 1:
            raise ValueError("ContractVersion.revision must be >= 1")

    def __str__(self) -> str:
        return f"{self.year}.{self.revision}"

    @property
    def id(self) -> str:
        """
        Canonical, stable identifier usable in logs, headers, manifests.
        """
        return f"contracts@{self}"
