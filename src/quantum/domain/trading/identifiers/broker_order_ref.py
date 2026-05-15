from dataclasses import dataclass

from quantum.domain.shared_kernel.foundation.errors.invariants import InvariantViolation
from quantum.domain.shared_kernel.modeling.value_objects.value_object import ValueObject
from quantum.domain.trading.identifiers.broker_account_id import BrokerAccountId
from quantum.domain.trading.identifiers.broker_venue_id import BrokerVenueId


@dataclass(frozen=True, slots=True)
class BrokerOrderRef(ValueObject):
    """
    Globally safe broker order reference.

    Prevents collisions across:
    - brokers
    - prop firms
    - accounts
    - terminals
    """

    venue_id: BrokerVenueId
    account_id: BrokerAccountId
    native_order_id: int

    def _validate_semantics(self) -> None:
        if not isinstance(self.venue_id, BrokerVenueId):
            raise InvariantViolation("BrokerOrderRef.venue_id must be BrokerVenueId")

        if not isinstance(self.account_id, BrokerAccountId):
            raise InvariantViolation(
                "BrokerOrderRef.account_id must be BrokerAccountId"
            )

        if type(self.native_order_id) is not int:
            raise InvariantViolation(
                "BrokerOrderRef.native_order_id must be a strict int"
            )

        if self.native_order_id < 1:
            raise InvariantViolation("BrokerOrderRef.native_order_id must be >= 1")

    def __str__(self) -> str:
        return f"{self.venue_id}:{self.account_id}:order:{self.native_order_id}"
