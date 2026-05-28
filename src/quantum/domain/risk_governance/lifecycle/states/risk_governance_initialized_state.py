from dataclasses import dataclass

from quantum.domain.market.calendar.utc_date import UtcDate
from quantum.domain.risk_governance.breach_detection.breaches.risk_breach import (
    RiskBreach,
)
from quantum.domain.risk_governance.lifecycle.states.risk_governance_state_base import (
    RiskGovernanceStateBase,
)
from quantum.domain.risk_governance.limits.risk_limits import RiskLimits
from quantum.domain.risk_governance.portfolio_state.risk_snapshot import RiskSnapshot
from quantum.domain.shared_kernel.foundation.errors.invariants import (
    CurrencyMismatch,
    InvariantViolation,
)


@dataclass(frozen=True, slots=True)
class RiskGovernanceInitializedState(RiskGovernanceStateBase):

    limits: RiskLimits
    snapshot: RiskSnapshot
    trading_day: UtcDate
    active_breaches: tuple[RiskBreach, ...] = ()

    def _validate_semantics(self) -> None:
        super()._validate_semantics()

        required_fields: tuple[tuple[str, object, type[object]], ...] = (
            ("limits", self.limits, RiskLimits),
            ("snapshot", self.snapshot, RiskSnapshot),
            ("trading_day", self.trading_day, UtcDate),
            ("active_breaches", self.active_breaches, tuple),
        )

        for field_name, value, expected_type in required_fields:
            if not isinstance(value, expected_type):
                raise InvariantViolation(
                    f"RiskGovernanceInitializedState.{field_name} invalid"
                )

        if self.last_sequence.is_initial():
            raise InvariantViolation("Initialized risk cannot be initial")

        if self.limits.context != self.snapshot.equity.context:
            raise InvariantViolation(
                "RiskLimits MoneyContext must match RiskSnapshot MoneyContext"
            )

        if self.snapshot.equity.currency != self.limits.context.reporting_currency:
            raise CurrencyMismatch(
                "RiskSnapshot currency must equal RiskLimits.context.reporting_currency"
            )

        for breach in self.active_breaches:
            if not isinstance(breach, RiskBreach):
                raise InvariantViolation(
                    "RiskGovernanceInitializedState.active_breaches must contain only RiskBreach"
                )
