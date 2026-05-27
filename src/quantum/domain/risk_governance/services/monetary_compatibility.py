from quantum.domain.shared_kernel.foundation.errors.invariants import (
    CurrencyMismatch,
    InvariantViolation,
)
from quantum.domain.shared_kernel.modeling.monetary.contextual_monetary_amount import (
    ContextualMonetaryAmount,
)
from quantum.domain.shared_kernel.modeling.monetary.money_context import MoneyContext
from quantum.domain.shared_kernel.modeling.services.domain_service import DomainService


class MonetaryCompatibilityService(DomainService):
    __slots__ = ()

    @staticmethod
    def assert_context(
        *,
        value: ContextualMonetaryAmount,
        expected_context: MoneyContext,
        label: str,
    ) -> None:
        if not isinstance(value, ContextualMonetaryAmount):
            raise InvariantViolation(f"{label} must be ContextualMonetaryAmount")

        if value.context != expected_context:
            raise InvariantViolation(f"{label} MoneyContext mismatch")

    @staticmethod
    def assert_reporting_currency(
        *,
        value: ContextualMonetaryAmount,
        expected_context: MoneyContext,
        label: str,
    ) -> None:
        MonetaryCompatibilityService.assert_context(
            value=value,
            expected_context=expected_context,
            label=label,
        )

        if value.currency != expected_context.reporting_currency:
            raise CurrencyMismatch(
                f"{label} currency must equal MoneyContext.reporting_currency"
            )

    @staticmethod
    def assert_same_context_and_currency(
        *,
        left: ContextualMonetaryAmount,
        right: ContextualMonetaryAmount,
        left_label: str,
        right_label: str,
    ) -> None:
        if left.context != right.context:
            raise InvariantViolation(
                f"{left_label}/{right_label} MoneyContext mismatch"
            )

        if left.currency != right.currency:
            raise CurrencyMismatch(f"{left_label}/{right_label} currency mismatch")
