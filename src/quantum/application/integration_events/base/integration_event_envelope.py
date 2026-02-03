from __future__ import annotations

import hashlib
import json

from dataclasses import asdict, dataclass
from typing import Any

from quantum.application.integration_events.base.integration_event import (
    IntegrationEvent,
)
from quantum.application.integration_events.base.integration_headers import (
    IntegrationHeaders,
)
from quantum.domain.shared_kernel.errors.invariants import InvariantViolation
from quantum.domain.shared_kernel.primitives.value_object import ValueObject
from quantum.domain.shared_kernel.value_objects.epoch_ms import EpochMs


@dataclass(frozen=True, slots=True)
class IntegrationEventEnvelope(ValueObject):
    """
    Transport-safe, audit-grade envelope for external communication.
    """

    headers: IntegrationHeaders
    payload: IntegrationEvent

    occurred_at: EpochMs
    published_at: EpochMs

    payload_hash: str

    def _validate(self) -> None:
        if not isinstance(self.headers, IntegrationHeaders):
            raise InvariantViolation("Invalid headers")

        if not isinstance(self.payload, IntegrationEvent):
            raise InvariantViolation("Invalid payload type")

        if self.published_at.value < self.occurred_at.value:
            raise InvariantViolation("published_at must be >= occurred_at")

        computed = self.compute_payload_hash(self.payload)
        if computed != self.payload_hash:
            raise InvariantViolation("Payload hash mismatch (corrupted envelope)")

    @staticmethod
    def compute_payload_hash(event: IntegrationEvent) -> str:
        canonical = json.dumps(
            asdict(event),
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
        ).encode("utf-8")

        return hashlib.sha256(canonical).hexdigest()

    @classmethod
    def create(
        cls,
        *,
        payload: IntegrationEvent,
        headers: IntegrationHeaders,
        occurred_at: EpochMs,
        published_at: EpochMs,
    ) -> IntegrationEventEnvelope:

        payload_hash = cls.compute_payload_hash(payload)

        return cls(
            headers=headers,
            payload=payload,
            occurred_at=occurred_at,
            published_at=published_at,
            payload_hash=payload_hash,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "headers": asdict(self.headers),
            "payload": asdict(self.payload),
            "occurred_at": self.occurred_at.value,
            "published_at": self.published_at.value,
            "payload_hash": self.payload_hash,
        }

    @classmethod
    def from_dict(
        cls, data: dict[str, Any], payload_type: type[IntegrationEvent]
    ) -> IntegrationEventEnvelope:

        headers = IntegrationHeaders(**data["headers"])

        payload = payload_type(**data["payload"])

        return cls(
            headers=headers,
            payload=payload,
            occurred_at=EpochMs(data["occurred_at"]),
            published_at=EpochMs(data["published_at"]),
            payload_hash=data["payload_hash"],
        )
