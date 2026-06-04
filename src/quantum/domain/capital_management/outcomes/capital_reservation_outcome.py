from __future__ import annotations

from dataclasses import dataclass

from quantum.domain.capital_management.allocation.capital_allocation_intent import (
    CapitalAllocationIntent,
)
from quantum.domain.capital_management.reservation.reason_codes.capital_reservation_rejection_reason_code import (
    CapitalReservationRejectionReasonCode,
)
from quantum.domain.shared_kernel.foundation.errors.invariants import InvariantViolation
from quantum.domain.shared_kernel.modeling.value_objects.value_object import ValueObject


@dataclass(frozen=True, slots=True)
class CapitalReservationOutcome(ValueObject):
    """
    Semantic domain outcome of a capital reservation attempt.

    Application handlers must consume this outcome instead of inspecting
    concrete CapitalReservation event types.
    """

    accepted: bool
    reserved_allocation: CapitalAllocationIntent | None
    rejection_reason_code: CapitalReservationRejectionReasonCode | None

    def _validate_types(self) -> None:
        if type(self.accepted) is not bool:
            raise InvariantViolation("CapitalReservationOutcome.accepted must be bool")

        if self.reserved_allocation is not None and not isinstance(
            self.reserved_allocation,
            CapitalAllocationIntent,
        ):
            raise InvariantViolation(
                "CapitalReservationOutcome.reserved_allocation must be "
                "CapitalAllocationIntent or None"
            )

        if self.rejection_reason_code is not None and not isinstance(
            self.rejection_reason_code,
            CapitalReservationRejectionReasonCode,
        ):
            raise InvariantViolation(
                "CapitalReservationOutcome.rejection_reason_code must be "
                "CapitalReservationRejectionReasonCode or None"
            )

    def _validate_semantics(self) -> None:
        self._validate_types()

        if self.accepted:
            if self.reserved_allocation is None:
                raise InvariantViolation(
                    "Accepted CapitalReservationOutcome requires reserved_allocation"
                )

            if self.rejection_reason_code is not None:
                raise InvariantViolation(
                    "Accepted CapitalReservationOutcome must not define rejection_reason_code"
                )

        else:
            if self.reserved_allocation is not None:
                raise InvariantViolation(
                    "Rejected CapitalReservationOutcome must not define reserved_allocation"
                )

            if self.rejection_reason_code is None:
                raise InvariantViolation(
                    "Rejected CapitalReservationOutcome requires rejection_reason_code"
                )

    @classmethod
    def accepted(
        cls,
        *,
        reserved_allocation: CapitalAllocationIntent,
    ) -> CapitalReservationOutcome:
        return cls(
            accepted=True,
            reserved_allocation=reserved_allocation,
            rejection_reason_code=None,
        )

    @classmethod
    def rejected(
        cls,
        *,
        rejection_reason_code: CapitalReservationRejectionReasonCode,
    ) -> CapitalReservationOutcome:
        return cls(
            accepted=False,
            reserved_allocation=None,
            rejection_reason_code=rejection_reason_code,
        )
