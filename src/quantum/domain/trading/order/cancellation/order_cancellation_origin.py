from __future__ import annotations

from dataclasses import dataclass

from quantum.domain.shared_kernel.modeling.value_objects.closed_set_value_object import (
    ClosedSetValueObject,
)


@dataclass(frozen=True, slots=True)
class OrderCancellationOrigin(ClosedSetValueObject):
    """
    Canonical source explaining WHERE the cancellation originated.
    """

    @classmethod
    def _allowed_values(cls) -> frozenset[str]:
        return frozenset(
            {
                "user",
                "strategy",
                "risk_engine",
                "broker",
                "execution_engine",
                "system",
                "scheduler",
                "unknown",
            }
        )

    @classmethod
    def user(cls) -> OrderCancellationOrigin:
        return cls("user")

    @classmethod
    def strategy(cls) -> OrderCancellationOrigin:
        return cls("strategy")

    @classmethod
    def risk_engine(cls) -> OrderCancellationOrigin:
        return cls("risk_engine")

    @classmethod
    def broker(cls) -> OrderCancellationOrigin:
        return cls("broker")

    @classmethod
    def system(cls) -> OrderCancellationOrigin:
        return cls("system")

    @classmethod
    def unknown(cls) -> OrderCancellationOrigin:
        return cls("unknown")
