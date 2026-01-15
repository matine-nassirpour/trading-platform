from __future__ import annotations

from dataclasses import dataclass

from quantum.domain.risk.events.v1.killswitch_armed_event import KillSwitchArmedEvent
from quantum.domain.risk.events.v1.killswitch_trigger_event import (
    KillSwitchTriggerEvent,
)
from quantum.domain.risk.value_objects.kill_switch_reason import KillSwitchReason
from quantum.domain.risk.value_objects.kill_switch_status import KillSwitchStatus
from quantum.domain.shared_kernel.errors.invariants import (
    InvalidStateTransition,
    InvariantViolation,
)
from quantum.domain.shared_kernel.events.event_envelope import EventEnvelope
from quantum.domain.shared_kernel.events.event_sequence import EventSequence
from quantum.domain.shared_kernel.primitives.aggregate_state import AggregateState
from quantum.domain.shared_kernel.primitives.event_sourced_aggregate_root import (
    EventSourcedAggregateRoot,
)


@dataclass(frozen=True, slots=True)
class KillSwitchStateData(AggregateState):
    """
    Immutable event-sourced state of the Kill Switch.

    Valid states:
    - Pre-genesis (status=None, reason=None)
    - Armed (status=armed, reason=None)
    - Triggered (status=triggered, reason=KillSwitchReason)
    """

    last_sequence: EventSequence
    status: KillSwitchStatus | None
    reason: KillSwitchReason | None

    def last_event_sequence(self) -> EventSequence:
        return self.last_sequence

    def _validate(self) -> None:
        if not isinstance(self.last_sequence, EventSequence):
            raise InvariantViolation(
                "KillSwitchStateData.last_sequence must be EventSequence"
            )

        if self.status is None:
            if self.reason is not None:
                raise InvariantViolation("Pre-genesis KillSwitch cannot have a reason")

        if self.status == KillSwitchStatus.armed():
            if self.reason is not None:
                raise InvariantViolation("Armed KillSwitch must not have a reason")

        if self.status == KillSwitchStatus.triggered():
            if self.reason is None:
                raise InvariantViolation("Triggered KillSwitch must have a reason")


class KillSwitchState(EventSourcedAggregateRoot[KillSwitchStateData]):
    """
    Fully event-sourced Kill Switch aggregate.

    Valid transitions:
        (none) → armed
        armed → triggered
    """

    # --- Factory --------------------------------------------------------------

    @staticmethod
    def initialize() -> KillSwitchState:
        """
        Creates a KillSwitch by replaying its mandatory genesis event.

        This is the ONLY legal way to create a KillSwitch.
        """
        return KillSwitchState.rehydrate(
            events=[KillSwitchArmedEvent()],
            empty_state=KillSwitchStateData.empty(),
        )

    # --- Commands -------------------------------------------------------------

    def trigger(
        self,
        *,
        reason: KillSwitchReason,
        detail: str | None = None,
    ) -> list:
        state = self.state

        if not isinstance(reason, KillSwitchReason):
            raise InvariantViolation("KillSwitch trigger requires KillSwitchReason")

        if state.status == KillSwitchStatus.triggered():
            raise InvalidStateTransition("KillSwitch already triggered")

        return [
            KillSwitchTriggerEvent(
                reason=reason,
                detail=detail,
            )
        ]

    # --- Event → State transitions --------------------------------------------

    @staticmethod
    def _apply_armed(
        state: KillSwitchStateData,
        event: KillSwitchArmedEvent,
        envelope: EventEnvelope,
    ) -> KillSwitchStateData:
        return KillSwitchStateData(
            last_sequence=envelope.sequence,
            status=KillSwitchStatus.armed(),
            reason=None,
        )

    @staticmethod
    def _apply_triggered(
        state: KillSwitchStateData,
        event: KillSwitchTriggerEvent,
        envelope: EventEnvelope,
    ) -> KillSwitchStateData:
        return KillSwitchStateData(
            last_sequence=envelope.sequence,
            status=KillSwitchStatus.triggered(),
            reason=event.reason,
        )

    @classmethod
    def _handlers(cls):
        return {
            KillSwitchArmedEvent: cls._apply_armed,
            KillSwitchTriggerEvent: cls._apply_triggered,
        }
