from __future__ import annotations

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
from quantum.domain.shared_kernel.primitives.event_sourced_aggregate_root import (
    EventSourcedAggregateRoot,
)


class KillSwitchState(EventSourcedAggregateRoot):
    """
    Fully event-sourced Kill Switch.

    All state MUST come from events.
    """

    status: KillSwitchStatus
    reason: KillSwitchReason | None

    # --- Commands -------------------------------------------------------------

    def trigger(
        self,
        *,
        reason: KillSwitchReason,
        detail: str | None = None,
    ) -> None:
        if self.status == KillSwitchStatus.triggered():
            raise InvalidStateTransition("KillSwitch already triggered")

        self._raise(
            KillSwitchTriggerEvent(
                reason=reason,
                detail=detail,
            )
        )

    # --- Event application ----------------------------------------------------

    def _apply_killswitcharmedevent(self, event: KillSwitchArmedEvent) -> None:
        self.status = KillSwitchStatus.armed()
        self.reason = None

    def _apply_killswitchtriggerevent(self, event: KillSwitchTriggerEvent) -> None:
        self.status = KillSwitchStatus.triggered()
        self.reason = event.reason

    # --- Invariants ----------------------------------------------------------

    def _validate_state(self) -> None:
        if not isinstance(self.status, KillSwitchStatus):
            raise InvariantViolation("KillSwitchState must have a valid status")

        if self.status == KillSwitchStatus.armed():
            if self.reason is not None:
                raise InvariantViolation(
                    "Armed KillSwitch must not have trigger metadata"
                )

        if self.status == KillSwitchStatus.triggered():
            if self.reason is None:
                raise InvariantViolation(
                    "Triggered KillSwitch must have a trigger reason"
                )
