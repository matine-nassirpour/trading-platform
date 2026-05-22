from dataclasses import dataclass

from quantum.domain.trading.identifiers.broker_entity_ref import BrokerEntityRef


@dataclass(frozen=True, slots=True)
class BrokerPositionRef(BrokerEntityRef):
    """
    Globally safe broker position reference.
    """

    @classmethod
    def entity_kind(cls) -> str:
        return "position"
