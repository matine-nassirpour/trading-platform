from dataclasses import dataclass

from quantum.domain.shared_kernel.modeling.value_objects.closed_set_value_object import (
    ClosedSetValueObject,
)


@dataclass(frozen=True, slots=True)
class KillSwitchReason(ClosedSetValueObject):
    """
    Canonical kill switch trigger reason.
    """

    @classmethod
    def _allowed_values(cls) -> frozenset[str]:
        return frozenset(
            {
                "risk_limit",
                "network",
                "broker_rejects",
                "manual",
            }
        )
