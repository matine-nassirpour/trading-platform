from collections.abc import Mapping
from dataclasses import dataclass

from quantum.domain.risk.events.v1.kill_switch.killswitch_armed_event import (
    KillSwitchArmedEvent,
)
from quantum.domain.risk.events.v1.kill_switch.killswitch_triggered_event import (
    KillSwitchTriggeredEvent,
)
from quantum.domain.risk.kill_switch.reason import KillSwitchReason
from quantum.domain.risk.kill_switch.states.kill_switch_armed_state import (
    KillSwitchArmedState,
)
from quantum.domain.risk.kill_switch.states.kill_switch_state_base import (
    KillSwitchStateBase,
)
from quantum.domain.risk.kill_switch.states.kill_switch_triggered_state import (
    KillSwitchTriggeredState,
)
from quantum.domain.risk.kill_switch.states.kill_switch_uninitialized_state import (
    KillSwitchUninitializedState,
)
from quantum.domain.shared_kernel.errors.invariants import (
    InvalidStateTransition,
    InvariantViolation,
)
from quantum.domain.shared_kernel.events.base.base_event import BaseEvent
from quantum.domain.shared_kernel.events.event_sequence import EventSequence
from quantum.domain.shared_kernel.events.recorded_event_envelope import (
    RecordedEventEnvelope,
)
from quantum.domain.shared_kernel.identifiers.aggregate_id import AggregateId
from quantum.domain.shared_kernel.primitives.event_sourced_aggregate_root import (
    EventHandler,
    EventSourcedAggregateRoot,
)


@dataclass(frozen=True, slots=True)
class KillSwitchStateId(AggregateId):
    """
    Identity of the CapitalReservation aggregate (event stream id).
    """

    pass


class KillSwitchState(
    EventSourcedAggregateRoot[KillSwitchStateId, KillSwitchStateBase]
):
    """
    Fully event-sourced Kill Switch aggregate.

    Valid transitions:
        (none) → armed
        armed → triggered
    """

    __slots__ = ()

    @classmethod
    def aggregate_id_type(cls) -> type[KillSwitchStateId]:
        return KillSwitchStateId

    @classmethod
    def state_type(cls) -> type[KillSwitchStateBase]:
        return KillSwitchStateBase

    @classmethod
    def uninitialized_state(cls) -> KillSwitchStateBase:
        return KillSwitchUninitializedState(
            last_sequence=EventSequence.initial(),
        )

    # --- Factory --------------------------------------------------------------

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
    ) -> list[BaseEvent]:

        state = self.state

        if isinstance(state, KillSwitchUninitializedState):
            raise InvalidStateTransition("KillSwitch not armed")

        if isinstance(state, KillSwitchTriggeredState):
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
        state: KillSwitchStateBase,
        event: BaseEvent,
        envelope: RecordedEventEnvelope,
    ) -> KillSwitchStateBase:

        if not isinstance(state, KillSwitchUninitializedState):
            raise InvariantViolation("KillSwitch already armed")

        assert isinstance(event, KillSwitchArmedEvent)

        return KillSwitchArmedState(last_sequence=envelope.sequence)

    @staticmethod
    def _apply_triggered(
        state: KillSwitchStateBase,
        event: BaseEvent,
        envelope: RecordedEventEnvelope,
    ) -> KillSwitchStateBase:

        if not isinstance(state, KillSwitchArmedState):
            raise InvariantViolation("KillSwitch not armed")

        assert isinstance(event, KillSwitchTriggeredEvent)

        return KillSwitchTriggeredState(
            last_sequence=envelope.sequence,
            reason=event.reason,
        )

    # --- Handler registry -----------------------------------------------------

    @classmethod
    def _handlers(
        cls,
    ) -> Mapping[type[BaseEvent], EventHandler[KillSwitchStateBase, BaseEvent]]:
        return {
            KillSwitchArmedEvent: cls._apply_armed,
            KillSwitchTriggeredEvent: cls._apply_triggered,
        }
