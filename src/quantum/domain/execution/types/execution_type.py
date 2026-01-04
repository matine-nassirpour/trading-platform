from __future__ import annotations

from typing import ClassVar

from quantum.domain.shared_kernel.primitives.closed_set_value_object import (
    ClosedSetValueObject,
)


class ExecutionType(ClosedSetValueObject):
    """
    Canonical execution type.

    Mirrors FIX ExecType semantics without infra coupling.
    """

    _ALLOWED_VALUES: ClassVar[frozenset[str]] = frozenset(
        {
            "new",
            "partial_fill",
            "fill",
            "cancel",
            "reject",
        }
    )

    # Optional named constructors (recommended)
    @classmethod
    def new(cls) -> ExecutionType:
        return cls("new")

    @classmethod
    def partial_fill(cls) -> ExecutionType:
        return cls("partial_fill")

    @classmethod
    def fill(cls) -> ExecutionType:
        return cls("fill")

    @classmethod
    def cancel(cls) -> ExecutionType:
        return cls("cancel")

    @classmethod
    def reject(cls) -> ExecutionType:
        return cls("reject")
