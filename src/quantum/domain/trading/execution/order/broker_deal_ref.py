from dataclasses import dataclass

from quantum.domain.shared_kernel.foundation.errors.invariants import InvariantViolation
from quantum.domain.shared_kernel.modeling.value_objects.value_object import ValueObject
from quantum.domain.trading.identifiers.broker_account_id import BrokerAccountId
from quantum.domain.trading.identifiers.broker_venue_id import BrokerVenueId


@dataclass(frozen=True, slots=True)
class BrokerDealRef(ValueObject):
    venue_id: BrokerVenueId
    account_id: BrokerAccountId
    native_deal_id: int

    def _validate_semantics(self) -> None:
        if not isinstance(self.venue_id, BrokerVenueId):
            raise InvariantViolation("BrokerDealRef.venue_id must be BrokerVenueId")

        if not isinstance(self.account_id, BrokerAccountId):
            raise InvariantViolation("BrokerDealRef.account_id must be BrokerAccountId")

        if type(self.native_deal_id) is not int:
            raise InvariantViolation(
                "BrokerDealRef.native_deal_id must be a strict int"
            )

        if self.native_deal_id < 1:
            raise InvariantViolation("BrokerDealRef.native_deal_id must be >= 1")

    def __str__(self) -> str:
        return f"{self.venue_id}:{self.account_id}:deal:{self.native_deal_id}"
