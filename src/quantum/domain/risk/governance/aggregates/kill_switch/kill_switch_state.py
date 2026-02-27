from collections.abc import Mapping

from quantum.domain.risk.events.v1.killswitch_armed_event import KillSwitchArmedEvent
from quantum.domain.risk.events.v1.killswitch_triggered_event import (
    KillSwitchTriggeredEvent,
)
from quantum.domain.risk.governance.aggregates.kill_switch.kill_switch_armed_state import (
    KillSwitchArmedState,
)
from quantum.domain.risk.governance.aggregates.kill_switch.kill_switch_state_base import (
    KillSwitchStateBase,
)
from quantum.domain.risk.governance.aggregates.kill_switch.kill_switch_triggered_state import (
    KillSwitchTriggeredState,
)
from quantum.domain.risk.governance.aggregates.kill_switch.kill_switch_uninitialized_state import (
    KillSwitchUninitializedState,
)
from quantum.domain.risk.governance.aggregates.kill_switch.reason import (
    KillSwitchReason,
)
from quantum.domain.shared_kernel.errors.invariants import (
    InvalidStateTransition,
    InvariantViolation,
)
from quantum.domain.shared_kernel.events.base.base_event import BaseEvent
from quantum.domain.shared_kernel.events.event_sequence import EventSequence
from quantum.domain.shared_kernel.events.persisted_event_envelope import (
    PersistedEventEnvelope,
)
from quantum.domain.shared_kernel.primitives.event_sourced_aggregate_root import (
    EventHandler,
    EventSourcedAggregateRoot,
)


class KillSwitchState(EventSourcedAggregateRoot[KillSwitchStateBase]):
    """
    Fully event-sourced Kill Switch aggregate.

    Valid transitions:
        (none) → armed
        armed → triggered
    """

    __slots__ = ()

    @classmethod
    def empty_state(cls) -> KillSwitchStateBase:
        return KillSwitchUninitializedState(last_sequence=EventSequence.initial())

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
        envelope: PersistedEventEnvelope,
    ) -> KillSwitchStateBase:

        if not isinstance(state, KillSwitchUninitializedState):
            raise InvariantViolation("KillSwitch already armed")

        assert isinstance(event, KillSwitchArmedEvent)

        return KillSwitchArmedState(last_sequence=envelope.sequence)

    @staticmethod
    def _apply_triggered(
        state: KillSwitchStateBase,
        event: BaseEvent,
        envelope: PersistedEventEnvelope,
    ) -> KillSwitchStateBase:

        if not isinstance(state, KillSwitchArmedState):
            raise InvariantViolation("KillSwitch not armed")

        assert isinstance(event, KillSwitchTriggeredEvent)

        return KillSwitchTriggeredState(
            last_sequence=envelope.sequence,
            reason=event.reason,
        )

    @classmethod
    def _handlers(
        cls,
    ) -> Mapping[type[BaseEvent], EventHandler]:
        return {
            KillSwitchArmedEvent: cls._apply_armed,
            KillSwitchTriggeredEvent: cls._apply_triggered,
        }
