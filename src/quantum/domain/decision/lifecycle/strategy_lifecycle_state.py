from __future__ import annotations

from dataclasses import dataclass

from quantum.domain.shared_kernel.ddd.value_objects.closed_set_value_object import (
    ClosedSetValueObject,
)


@dataclass(frozen=True, slots=True)
class StrategyLifecycleState(ClosedSetValueObject):
    """
    Canonical lifecycle state of a trading strategy or model.

    Semantics:
    - Determines whether decisions are AUTHORIZED
    - Independent from performance or signals
    """

    @classmethod
    def _allowed_values(cls) -> frozenset[str]:
        return frozenset(
            {
                "inactive",  # defined but not tradable
                "active",  # fully authorized
                "deprecated",  # allowed but discouraged / limited
                "suspended",  # temporarily forbidden
                "sunset",  # permanently forbidden (historical only)
            }
        )

    # --- Named constructors ---------------------------------------------------

    @classmethod
    def inactive(cls) -> StrategyLifecycleState:
        return cls("inactive")

    @classmethod
    def active(cls) -> StrategyLifecycleState:
        return cls("active")

    @classmethod
    def deprecated(cls) -> StrategyLifecycleState:
        return cls("deprecated")

    @classmethod
    def suspended(cls) -> StrategyLifecycleState:
        return cls("suspended")

    @classmethod
    def sunset(cls) -> StrategyLifecycleState:
        return cls("sunset")

    # --- Semantic helpers -----------------------------------------------------

    def is_authorized(self) -> bool:
        return self.value in {"active", "deprecated"}

    def is_terminal(self) -> bool:
        return self.value == "sunset"
