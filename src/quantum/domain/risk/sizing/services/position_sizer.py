from __future__ import annotations

from dataclasses import dataclass
from decimal import ROUND_FLOOR, Decimal

from quantum.domain.market.instrument.instrument_spec import InstrumentSpec
from quantum.domain.market.instrument.pricing.reference_price import ReferencePrice
from quantum.domain.risk.capital.allocation.capital_allocation_intent import (
    CapitalAllocationIntent,
)
from quantum.domain.risk.governance.measures.equity import Equity
from quantum.domain.risk.sizing.reason_codes.position_sizing_rejection_reason_code import (
    PositionSizingRejectionReasonCode,
)
from quantum.domain.risk.sizing.value_objects.position_sizing_result import (
    PositionSizingResult,
)
from quantum.domain.risk.sizing.value_objects.position_volume import PositionVolume
from quantum.domain.risk.sizing.value_objects.risk_amount import RiskAmount
from quantum.domain.risk.sizing.value_objects.sizing_rounding_policy import (
    SizingRoundingPolicy,
)
from quantum.domain.risk.sizing.value_objects.stop_distance import StopDistance
from quantum.domain.shared_kernel.foundation.errors.invariants import (
    CurrencyMismatch,
    InvariantViolation,
)
from quantum.domain.shared_kernel.modeling.services.domain_service import DomainService
from quantum.domain.shared_kernel.modeling.value_objects.value_object import ValueObject


@dataclass(frozen=True, slots=True)
class PositionSizingEvaluation(ValueObject):
    """
    Algebraic result of a sizing evaluation.

    Exactly one of:
    - result
    - rejection_reason
    must be present.
    """

    result: PositionSizingResult | None
    rejection_reason: PositionSizingRejectionReasonCode | None

    def _validate_semantics(self) -> None:
        if self.result is None and self.rejection_reason is None:
            raise InvariantViolation(
                "PositionSizingEvaluation must contain result or rejection_reason"
            )

        if self.result is not None and self.rejection_reason is not None:
            raise InvariantViolation(
                "PositionSizingEvaluation cannot contain both result and rejection_reason"
            )

        if self.result is not None and not isinstance(
            self.result, PositionSizingResult
        ):
            raise InvariantViolation("PositionSizingEvaluation.result invalid")

        if self.rejection_reason is not None and not isinstance(
            self.rejection_reason,
            PositionSizingRejectionReasonCode,
        ):
            raise InvariantViolation(
                "PositionSizingEvaluation.rejection_reason invalid"
            )

    def is_sized(self) -> bool:
        return self.result is not None

    def is_rejected(self) -> bool:
        return self.rejection_reason is not None

    @staticmethod
    def sized(result: PositionSizingResult) -> PositionSizingEvaluation:
        return PositionSizingEvaluation(result=result, rejection_reason=None)

    @staticmethod
    def rejected(
        reason: PositionSizingRejectionReasonCode,
    ) -> PositionSizingEvaluation:
        return PositionSizingEvaluation(result=None, rejection_reason=reason)


@dataclass(frozen=True, slots=True)
class _ComputedSizing:
    risk_amount_value: Decimal
    raw_volume: Decimal
    min_volume: Decimal
    max_volume: Decimal
    volume_step: Decimal


class PositionSizer(DomainService):
    """
    Pure domain service converting an authorized allocation intent into
    a risk-approved position volume.

    Formula:

        risk_amount = equity × risk_budget_slice

        risk_per_volume =
            stop_distance / tick_size × tick_value

        raw_volume_by_risk =
            risk_amount / risk_per_volume

        raw_volume_by_capital =
            allocated_capital / (reference_price × contract_size)

        raw_volume =
            min(raw_volume_by_risk, raw_volume_by_capital)

    Conservative doctrine:
        The service must never round volume upward.
    """

    __slots__ = ()

    # --- Volume utilities -----------------------------------------------------

    @staticmethod
    def _floor_to_volume_step(
        *,
        raw_volume: Decimal,
        min_volume: Decimal,
        volume_step: Decimal,
    ) -> Decimal:
        if raw_volume < min_volume:
            return Decimal("0")

        steps = ((raw_volume - min_volume) / volume_step).to_integral_value(
            rounding=ROUND_FLOOR
        )

        return min_volume + steps * volume_step

    @staticmethod
    def _is_step_aligned(
        *,
        volume: Decimal,
        min_volume: Decimal,
        volume_step: Decimal,
    ) -> bool:
        if volume < min_volume:
            return False

        return ((volume - min_volume) / volume_step) == (
            (volume - min_volume) / volume_step
        ).to_integral_value()

    # --- Internal Helpers -----------------------------------------------------

    @staticmethod
    def _validate_context(
        *,
        equity: Equity,
        instrument: InstrumentSpec,
    ) -> None:
        if equity.context != instrument.context:
            raise InvariantViolation("Equity MoneyContext mismatch with instrument")

        if equity.currency != instrument.context.reporting_currency:
            raise CurrencyMismatch(
                "Equity currency must match instrument reporting currency"
            )

    @staticmethod
    def _reject_invalid_inputs(
        *,
        equity: Equity,
        stop_distance: StopDistance,
        instrument: InstrumentSpec,
    ) -> PositionSizingEvaluation | None:
        if equity.value <= Decimal("0"):
            return PositionSizingEvaluation.rejected(
                PositionSizingRejectionReasonCode.non_positive_equity()
            )

        if stop_distance.value <= Decimal("0"):
            return PositionSizingEvaluation.rejected(
                PositionSizingRejectionReasonCode.invalid_stop_distance()
            )

        if stop_distance.value < instrument.constraints.price.stop_level:
            return PositionSizingEvaluation.rejected(
                PositionSizingRejectionReasonCode.stop_distance_below_broker_minimum()
            )

        return None

    @staticmethod
    def _compute_risk_limited_volume(
        *,
        allocation: CapitalAllocationIntent,
        equity: Equity,
        stop_distance: StopDistance,
        instrument: InstrumentSpec,
    ) -> Decimal | PositionSizingEvaluation:
        risk_amount_value = equity.value * allocation.risk_budget.value

        if risk_amount_value <= Decimal("0"):
            return PositionSizingEvaluation.rejected(
                PositionSizingRejectionReasonCode.risk_amount_too_small()
            )

        microstructure = instrument.microstructure
        tick_count = stop_distance.value / microstructure.tick_size.value
        risk_per_volume = tick_count * microstructure.tick_value.value

        if risk_per_volume <= Decimal("0"):
            return PositionSizingEvaluation.rejected(
                PositionSizingRejectionReasonCode.sizing_policy_violation()
            )

        return risk_amount_value / risk_per_volume

    @staticmethod
    def _compute_capital_limited_volume(
        *,
        allocation: CapitalAllocationIntent,
        equity: Equity,
        instrument: InstrumentSpec,
        reference_price: ReferencePrice,
    ) -> Decimal | PositionSizingEvaluation:
        microstructure = instrument.microstructure
        allocated_capital = equity.value * allocation.capital_fraction.value
        notional_per_volume = reference_price.value * microstructure.contract_size.value

        if notional_per_volume <= Decimal("0"):
            return PositionSizingEvaluation.rejected(
                PositionSizingRejectionReasonCode.sizing_policy_violation()
            )

        raw_volume_by_capital = allocated_capital / notional_per_volume

        if raw_volume_by_capital <= Decimal("0"):
            return PositionSizingEvaluation.rejected(
                PositionSizingRejectionReasonCode.notional_capacity_exhausted()
            )

        return raw_volume_by_capital

    @staticmethod
    def _compute_sizing(
        *,
        allocation: CapitalAllocationIntent,
        equity: Equity,
        stop_distance: StopDistance,
        instrument: InstrumentSpec,
        reference_price: ReferencePrice,
    ) -> _ComputedSizing | PositionSizingEvaluation:
        raw_volume_by_risk = PositionSizer._compute_risk_limited_volume(
            allocation=allocation,
            equity=equity,
            stop_distance=stop_distance,
            instrument=instrument,
        )

        if isinstance(raw_volume_by_risk, PositionSizingEvaluation):
            return raw_volume_by_risk

        raw_volume_by_capital = PositionSizer._compute_capital_limited_volume(
            allocation=allocation,
            equity=equity,
            instrument=instrument,
            reference_price=reference_price,
        )

        if isinstance(raw_volume_by_capital, PositionSizingEvaluation):
            return raw_volume_by_capital

        volume_constraints = instrument.constraints.volume

        return _ComputedSizing(
            risk_amount_value=equity.value * allocation.risk_budget.value,
            raw_volume=min(raw_volume_by_risk, raw_volume_by_capital),
            min_volume=volume_constraints.min_volume,
            max_volume=volume_constraints.max_volume,
            volume_step=volume_constraints.volume_step,
        )

    @staticmethod
    def _cap_to_max_volume(computed: _ComputedSizing) -> Decimal:
        if computed.raw_volume > computed.max_volume:
            return computed.max_volume

        return computed.raw_volume

    @staticmethod
    def _round_volume(
        *,
        computed: _ComputedSizing,
        rounding_policy: SizingRoundingPolicy,
    ) -> Decimal | PositionSizingEvaluation:
        raw_volume = PositionSizer._cap_to_max_volume(computed)

        if raw_volume < computed.min_volume:
            return PositionSizingEvaluation.rejected(
                PositionSizingRejectionReasonCode.volume_below_minimum()
            )

        if rounding_policy.rejects_if_not_exact():
            return PositionSizer._reject_or_accept_exact_volume(
                raw_volume=raw_volume,
                computed=computed,
            )

        return PositionSizer._floor_to_volume_step(
            raw_volume=raw_volume,
            min_volume=computed.min_volume,
            volume_step=computed.volume_step,
        )

    @staticmethod
    def _reject_or_accept_exact_volume(
        *,
        raw_volume: Decimal,
        computed: _ComputedSizing,
    ) -> Decimal | PositionSizingEvaluation:
        if not PositionSizer._is_step_aligned(
            volume=raw_volume,
            min_volume=computed.min_volume,
            volume_step=computed.volume_step,
        ):
            return PositionSizingEvaluation.rejected(
                PositionSizingRejectionReasonCode.volume_not_step_aligned()
            )

        return raw_volume

    @staticmethod
    def _reject_invalid_final_volume(
        *,
        final_volume: Decimal,
        computed: _ComputedSizing,
    ) -> PositionSizingEvaluation | None:
        if final_volume < computed.min_volume:
            return PositionSizingEvaluation.rejected(
                PositionSizingRejectionReasonCode.volume_below_minimum()
            )

        if final_volume > computed.max_volume:
            return PositionSizingEvaluation.rejected(
                PositionSizingRejectionReasonCode.volume_above_maximum()
            )

        return None

    @staticmethod
    def _build_result(
        *,
        final_volume: Decimal,
        computed: _ComputedSizing,
        equity: Equity,
    ) -> PositionSizingEvaluation:
        risk_amount = RiskAmount(
            value=computed.risk_amount_value,
            currency=equity.currency,
            context=equity.context,
        )

        result = PositionSizingResult(
            risk_amount=risk_amount,
            volume=PositionVolume(final_volume),
        )

        return PositionSizingEvaluation.sized(result)

    # --- Public API -----------------------------------------------------------

    @staticmethod
    def evaluate(
        *,
        allocation: CapitalAllocationIntent,
        equity: Equity,
        stop_distance: StopDistance,
        instrument: InstrumentSpec,
        reference_price: ReferencePrice,
        rounding_policy: SizingRoundingPolicy,
    ) -> PositionSizingEvaluation:
        PositionSizer._validate_context(equity=equity, instrument=instrument)

        rejection = PositionSizer._reject_invalid_inputs(
            equity=equity,
            stop_distance=stop_distance,
            instrument=instrument,
        )
        if rejection is not None:
            return rejection

        computed = PositionSizer._compute_sizing(
            allocation=allocation,
            equity=equity,
            stop_distance=stop_distance,
            instrument=instrument,
            reference_price=reference_price,
        )
        if isinstance(computed, PositionSizingEvaluation):
            return computed

        final_volume = PositionSizer._round_volume(
            computed=computed,
            rounding_policy=rounding_policy,
        )
        if isinstance(final_volume, PositionSizingEvaluation):
            return final_volume

        rejection = PositionSizer._reject_invalid_final_volume(
            final_volume=final_volume,
            computed=computed,
        )
        if rejection is not None:
            return rejection

        return PositionSizer._build_result(
            final_volume=final_volume,
            computed=computed,
            equity=equity,
        )
