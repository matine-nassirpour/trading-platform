from abc import ABC, abstractmethod
from dataclasses import dataclass

from quantum.domain.shared_kernel.foundation.errors.invariants import InvariantViolation
from quantum.domain.shared_kernel.modeling.value_objects.value_object import ValueObject
from quantum.domain.trading.identity.broker_account_id import BrokerAccountId
from quantum.domain.trading.identity.broker_venue_id import BrokerVenueId


@dataclass(frozen=True, slots=True)
class BrokerEntityRef(ValueObject, ABC):
    """
    Canonical broker-side entity reference.

    Prevents native broker identifier collisions across:
    - venues
    - prop firms
    - broker accounts
    - terminals
    - entity kinds

    Concrete subclasses define the semantic entity kind:
    - order
    - position
    - deal
    """

    venue_id: BrokerVenueId
    account_id: BrokerAccountId
    native_id: int

    @classmethod
    @abstractmethod
    def entity_kind(cls) -> str:
        """
        Canonical broker entity kind.

        Examples:
            - order
            - position
            - deal
        """
        raise NotImplementedError

    def _validate_semantics(self) -> None:
        if not isinstance(self.venue_id, BrokerVenueId):
            raise InvariantViolation(
                f"{self.__class__.__name__}.venue_id must be BrokerVenueId"
            )

        if not isinstance(self.account_id, BrokerAccountId):
            raise InvariantViolation(
                f"{self.__class__.__name__}.account_id must be BrokerAccountId"
            )

        if type(self.native_id) is not int:
            raise InvariantViolation(
                f"{self.__class__.__name__}.native_id must be a strict int"
            )

        if self.native_id < 1:
            raise InvariantViolation(
                f"{self.__class__.__name__}.native_id must be >= 1"
            )

        kind = self.entity_kind()

        if not isinstance(kind, str):
            raise InvariantViolation(
                f"{self.__class__.__name__}.entity_kind() must return str"
            )

        if kind != kind.strip().lower() or not kind:
            raise InvariantViolation(
                f"{self.__class__.__name__}.entity_kind() must be canonical lowercase"
            )

    def __str__(self) -> str:
        return (
            f"{self.venue_id}:{self.account_id}:{self.entity_kind()}:{self.native_id}"
        )
