from dataclasses import dataclass


@dataclass(frozen=True)
class ContractVersion:
    """
    Semantic, immutable contract version.

    Rules:
    - bump on backward-incompatible change
    - never modified retroactively
    """

    year: int
    revision: int

    def __str__(self) -> str:
        return f"{self.year}.{self.revision}"
