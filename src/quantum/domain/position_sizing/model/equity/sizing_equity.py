from dataclasses import dataclass

from quantum.domain.shared_kernel.modeling.monetary.contextual_monetary_amount import (
    ContextualMonetaryAmount,
)


@dataclass(frozen=True, slots=True)
class SizingEquity(ContextualMonetaryAmount):
    """
    Equity value as seen by the position_sizing BC.

    This is intentionally NOT risk_governance.Equity.
    """

    @classmethod
    def nominal_type(cls) -> str:
        return "sizing_equity"

    def _validate_numeric_semantics(self) -> None:
        super()._validate_numeric_semantics()

        # Negative or zero equity is handled as rejection by the sizing service,
        # not forbidden here, so the domain can explain the rejection.
        return None
