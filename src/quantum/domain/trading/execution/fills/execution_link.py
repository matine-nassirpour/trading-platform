from dataclasses import dataclass

from quantum.domain.shared_kernel.foundation.errors.invariants import InvariantViolation
from quantum.domain.shared_kernel.modeling.value_objects.value_object import ValueObject
from quantum.domain.trading.identity.broker_deal_ref import BrokerDealRef
from quantum.domain.trading.identity.broker_order_ref import BrokerOrderRef
from quantum.domain.trading.identity.broker_position_ref import BrokerPositionRef


@dataclass(frozen=True, slots=True)
class ExecutionLink(ValueObject):
    """
    Explicit broker-side audit link for one execution fill.

    Purpose:
    - order reconciliation
    - deal reconciliation
    - optional position reconciliation
    - broker audit trail
    """

    broker_order_ref: BrokerOrderRef
    broker_deal_ref: BrokerDealRef
    broker_position_ref: BrokerPositionRef | None = None

    def _validate_types(self) -> None:
        required_fields: tuple[tuple[str, object, type[object]], ...] = (
            ("broker_order_ref", self.broker_order_ref, BrokerOrderRef),
            ("broker_deal_ref", self.broker_deal_ref, BrokerDealRef),
        )

        for field_name, value, expected_type in required_fields:
            if not isinstance(value, expected_type):
                raise InvariantViolation(f"ExecutionLink.{field_name} invalid")

    def _validate_semantics(self) -> None:
        self._validate_types()

        if self.broker_position_ref is not None and not isinstance(
            self.broker_position_ref,
            BrokerPositionRef,
        ):
            raise InvariantViolation("ExecutionLink.broker_position_ref invalid")

        if self.broker_order_ref.venue_id != self.broker_deal_ref.venue_id:
            raise InvariantViolation("ExecutionLink venue mismatch")

        if self.broker_order_ref.account_id != self.broker_deal_ref.account_id:
            raise InvariantViolation("ExecutionLink account mismatch")

        if self.broker_position_ref is not None:
            if self.broker_position_ref.venue_id != self.broker_order_ref.venue_id:
                raise InvariantViolation("ExecutionLink position venue mismatch")

            if self.broker_position_ref.account_id != self.broker_order_ref.account_id:
                raise InvariantViolation("ExecutionLink position account mismatch")
