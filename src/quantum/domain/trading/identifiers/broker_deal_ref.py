from dataclasses import dataclass

from quantum.domain.trading.identifiers.broker_entity_ref import BrokerEntityRef


@dataclass(frozen=True, slots=True)
class BrokerDealRef(BrokerEntityRef):
    """
    Globally safe broker deal reference.
    """

    @classmethod
    def entity_kind(cls) -> str:
        return "deal"
