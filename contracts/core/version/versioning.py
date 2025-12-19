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
        # Year must be a valid, modern calendar year (epoch-based lower bound)
        if not isinstance(self.year, int):
            raise TypeError("ContractVersion.year must be an int")

        if self.year < 1970:
            raise ValueError(
                "ContractVersion.year must be >= 1970 "
                "(Unix epoch lower bound for modern systems)"
            )

        # Revision must be a positive integer
        if not isinstance(self.revision, int):
            raise TypeError("ContractVersion.revision must be an int")

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
