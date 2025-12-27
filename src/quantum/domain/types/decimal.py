from decimal import Decimal

from quantum.domain.model.exceptions.validation_exceptions import InvariantViolation


def require_positive(value: Decimal, name: str) -> None:
    if value <= 0:
        raise InvariantViolation(f"{name} must be > 0")


def require_non_negative(value: Decimal, name: str) -> None:
    if value < 0:
        raise InvariantViolation(f"{name} must be ≥ 0")
