from dataclasses import dataclass

from quantum.domain.shared_kernel.modeling.value_objects.closed_set_value_object import (
    ClosedSetValueObject,
)


@dataclass(frozen=True, slots=True)
class Currency(ClosedSetValueObject):
    """
    Canonical domain currency.

    IMPORTANT:
    - This is NOT ISO-4217.
    - This is the desk's internal canonical currency set.
    - Any external broker or feed currency must be mapped to this
      set via an Anti-Corruption Layer in the interfaces/infrastructure layer.
    """

    @classmethod
    def _allowed_values(cls) -> frozenset[str]:
        """
        Returns the complete finite set of currencies
        allowed by the trading desk.
        """
        return frozenset(
            {
                "usd",
                "eur",
                "jpy",
                "chf",
                "gbp",
                "cad",
                "aud",
                "nzd",
            }
        )
