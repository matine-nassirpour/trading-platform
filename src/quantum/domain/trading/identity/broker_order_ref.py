from dataclasses import dataclass

from quantum.domain.trading.identity.broker_entity_ref import BrokerEntityRef


@dataclass(frozen=True, slots=True)
class BrokerOrderRef(BrokerEntityRef):
    """
    Globally safe broker order reference.
    """

    @classmethod
    def entity_kind(cls) -> str:
        return "order"
