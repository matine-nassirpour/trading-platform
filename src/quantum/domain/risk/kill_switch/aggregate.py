from collections.abc import Mapping

from quantum.domain.risk.kill_switch.detail import KillSwitchDetail
from quantum.domain.risk.kill_switch.events.killswitch_armed_event import (
    KillSwitchArmedEvent,
)
from quantum.domain.risk.kill_switch.events.killswitch_triggered_event import (
    KillSwitchTriggeredEvent,
)
from quantum.domain.risk.kill_switch.kill_switch_id import KillSwitchId
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
from quantum.domain.shared_kernel.event_sourcing.aggregates.event_sourced_aggregate_root import (
    EventHandler,
    EventSourcedAggregateRoot,
)
from quantum.domain.shared_kernel.event_sourcing.events.base_event import BaseEvent
from quantum.domain.shared_kernel.event_sourcing.events.event_sequence import (
    EventSequence,
)
from quantum.domain.shared_kernel.event_sourcing.events.recorded_event_envelope import (
    RecordedEventEnvelope,
)
from quantum.domain.shared_kernel.foundation.errors.invariants import (
    InvalidStateTransition,
    InvariantViolation,
)


class KillSwitch(EventSourcedAggregateRoot[KillSwitchId, KillSwitchStateBase]):
    """
    Fully event-sourced Kill Switch aggregate.

    Valid transitions:
        (none) → armed
        armed → triggered
    """

    __slots__ = ()

    @classmethod
    def aggregate_id_type(cls) -> type[KillSwitchId]:
        return KillSwitchId

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
        detail: KillSwitchDetail | None = None,
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

        if not isinstance(event, KillSwitchArmedEvent):
            raise InvariantViolation(
                "KillSwitchState._apply_armed requires KillSwitchArmedEvent"
            )

        return KillSwitchArmedState(last_sequence=envelope.sequence)

    @staticmethod
    def _apply_triggered(
        state: KillSwitchStateBase,
        event: BaseEvent,
        envelope: RecordedEventEnvelope,
    ) -> KillSwitchStateBase:

        if not isinstance(state, KillSwitchArmedState):
            raise InvariantViolation("KillSwitch not armed")

        if not isinstance(event, KillSwitchTriggeredEvent):
            raise InvariantViolation(
                "KillSwitchState._apply_triggered requires KillSwitchTriggeredEvent"
            )

        return KillSwitchTriggeredState(
            last_sequence=envelope.sequence,
            reason=event.reason,
            detail=event.detail,
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
