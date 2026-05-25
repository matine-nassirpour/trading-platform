from __future__ import annotations

from dataclasses import dataclass

from quantum.domain.shared_kernel.modeling.value_objects.closed_set_value_object import (
    ClosedSetValueObject,
)


@dataclass(frozen=True, slots=True)
class VolumeUnit(ClosedSetValueObject):
    """
    Canonical instrument volume unit.

    Examples:
    - lot      : broker lot
    - contract : futures/CFD contract
    - share    : equity share
    - unit     : base asset unit
    """

    @classmethod
    def _allowed_values(cls) -> frozenset[str]:
        return frozenset({"lot", "contract", "share", "unit"})

    @classmethod
    def lot(cls) -> VolumeUnit:
        return cls("lot")

    @classmethod
    def contract(cls) -> VolumeUnit:
        return cls("contract")

    @classmethod
    def share(cls) -> VolumeUnit:
        return cls("share")

    @classmethod
    def unit(cls) -> VolumeUnit:
        return cls("unit")
