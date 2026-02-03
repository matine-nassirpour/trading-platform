import json

from typing import Any

from quantum.application.integration_events.base.integration_event_envelope import (
    IntegrationEventEnvelope,
)


class IntegrationEventSerializer:
    """
    Deterministic serialization format for integration events.
    """

    @staticmethod
    def serialize(envelope: IntegrationEventEnvelope) -> bytes:
        return json.dumps(
            envelope.to_dict(),
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
        ).encode("utf-8")

    @staticmethod
    def deserialize(data: bytes, payload_type: Any) -> IntegrationEventEnvelope:
        decoded = json.loads(data.decode("utf-8"))
        return IntegrationEventEnvelope.from_dict(decoded, payload_type)
