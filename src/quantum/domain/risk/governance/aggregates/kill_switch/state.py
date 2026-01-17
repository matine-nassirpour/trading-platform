from __future__ import annotations

from dataclasses import dataclass

from quantum.domain.risk.events.v1.killswitch_armed_event import KillSwitchArmedEvent
from quantum.domain.risk.events.v1.killswitch_triggered_event import (
    KillSwitchTriggeredEvent,
)
from quantum.domain.risk.governance.aggregates.kill_switch.reason import (
    KillSwitchReason,
)
from quantum.domain.risk.governance.aggregates.kill_switch.status import (
    KillSwitchStatus,
)
from quantum.domain.shared_kernel.errors.invariants import (
    InvalidStateTransition,
    InvariantViolation,
)
from quantum.domain.shared_kernel.events.base_event import BaseEvent
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

    @staticmethod
    def empty() -> KillSwitchStateData:
        """
        Canonical pre-genesis empty state.

        This state represents the aggregate BEFORE any event
        has been applied. It must only be used as the starting
        point for event replay.
        """
        return KillSwitchStateData(
            last_sequence=EventSequence.initial(),
            status=None,
            reason=None,
        )


class KillSwitchState(EventSourcedAggregateRoot[KillSwitchStateData]):
    """
    Fully event-sourced Kill Switch aggregate.

    Valid transitions:
        (none) → armed
        armed → triggered
    """

    # --- Factory --------------------------------------------------------------

    @staticmethod
    def empty() -> KillSwitchState:
        return KillSwitchState(KillSwitchStateData.empty())

    @staticmethod
    def genesis_events() -> list[BaseEvent]:
        """
        Canonical genesis events for the KillSwitch aggregate.
        """
        return [KillSwitchArmedEvent()]

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
            KillSwitchTriggeredEvent(
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
        event: KillSwitchTriggeredEvent,
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
            KillSwitchTriggeredEvent: cls._apply_triggered,
        }
