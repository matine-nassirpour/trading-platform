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
from quantum.domain.shared_kernel.primitives.aggregate_state import AggregateState
from quantum.domain.shared_kernel.primitives.event_sourced_aggregate_root import (
    EventSourcedAggregateRoot,
)


@dataclass(frozen=True, slots=True)
class KillSwitchStateData(AggregateState):
    """
    Immutable event-sourced state of the Kill Switch.
    """

    status: KillSwitchStatus
    reason: KillSwitchReason | None

    def _state_contract(self) -> None:
        pass


class KillSwitchState(EventSourcedAggregateRoot[KillSwitchStateData]):
    """
    Fully event-sourced Kill Switch aggregate.

    Valid state transitions:
        (none) → armed
        armed → triggered
    """

    # --- Factory --------------------------------------------------------------

    @staticmethod
    def initialize() -> KillSwitchState:
        """
        A KillSwitch MUST start armed.

        This is encoded by emitting the KillSwitchArmedEvent
        as the genesis event.
        """
        empty = KillSwitchStateData(
            status=KillSwitchStatus.armed(),
            reason=None,
        )

        return KillSwitchState(empty)

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
    ) -> KillSwitchStateData:
        return KillSwitchStateData(
            status=KillSwitchStatus.armed(),
            reason=None,
        )

    @staticmethod
    def _apply_triggered(
        state: KillSwitchStateData,
        event: KillSwitchTriggerEvent,
    ) -> KillSwitchStateData:
        return KillSwitchStateData(
            status=KillSwitchStatus.triggered(),
            reason=event.reason,
        )

    @classmethod
    def _handlers(cls):
        return {
            KillSwitchArmedEvent: cls._apply_armed,
            KillSwitchTriggerEvent: cls._apply_triggered,
        }

    # --- Invariants ----------------------------------------------------------

    def _validate_state(self) -> None:
        s = self.state

        if not isinstance(s.status, KillSwitchStatus):
            raise InvariantViolation("KillSwitchState must have a valid status")

        if s.status == KillSwitchStatus.armed():
            if s.reason is not None:
                raise InvariantViolation(
                    "Armed KillSwitch must not have trigger metadata"
                )

        if s.status == KillSwitchStatus.triggered():
            if s.reason is None:
                raise InvariantViolation(
                    "Triggered KillSwitch must have a trigger reason"
                )
