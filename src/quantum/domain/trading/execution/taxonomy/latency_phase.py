from typing import ClassVar

from quantum.domain.shared_kernel.architecture.domain_charter import DomainRole
from quantum.domain.shared_kernel.primitives.closed_set_value_object import (
    ClosedSetValueObject,
)


class LatencyPhase(ClosedSetValueObject):
    """
    Execution latency measurement phase.
    """

    _ALLOWED_VALUES: ClassVar[frozenset[str]] = frozenset(
        {
            "terminal_ping",
            "order_check",
            "order_send",
            "ack",
            "fill",
        }
    )

    def _closed_set_type(self) -> None:
        pass

    @classmethod
    def role(cls) -> DomainRole:
        return DomainRole.VALUE_OBJECT
