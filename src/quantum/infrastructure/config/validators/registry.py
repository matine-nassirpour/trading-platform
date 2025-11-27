from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from quantum.infrastructure.config.validators.base import (
    ValidationContext,
    ValidationResult,
    ValidationRule,
)


class ValidatorRegistry:
    """
    Immutable, safety-critical-grade registry of validation rules.

    Properties:
        • Deterministic once sealed
        • No mutation allowed after creation
        • No implicit global state
        • Suitable for multiprocess, multi-thread, Clean Architecture
    """

    __slots__ = ("_rules", "_sealed")

    def __init__(self) -> None:
        self._rules: dict[str, ValidationRule] = {}
        self._sealed: bool = False

    # --------------------------------------------------------------------------
    # Registration (allowed only before sealing)
    # --------------------------------------------------------------------------
    def register(self, rule: ValidationRule) -> None:
        if self._sealed:
            raise RuntimeError("Cannot register a rule on a sealed ValidatorRegistry.")

        if rule.rule_id in self._rules:
            raise ValueError(f"Duplicate validator id: {rule.rule_id}")

        self._rules[rule.rule_id] = rule

    def register_many(self, rules: Mapping[str, ValidationRule]) -> None:
        for rule in rules.values():
            self.register(rule)

    # --------------------------------------------------------------------------
    # Seal (make immutable)
    # --------------------------------------------------------------------------
    def seal(self) -> None:
        """
        Seal the registry permanently. No further modification possible.
        Deterministic = required for safety-critical certainty.
        """
        self._rules = dict(sorted(self._rules.items()))
        self._sealed = True

    # --------------------------------------------------------------------------
    # Lookup
    # --------------------------------------------------------------------------
    def get(self, rule_id: str) -> ValidationRule:
        try:
            return self._rules[rule_id]
        except KeyError as e:
            raise KeyError(f"Validator not found: {rule_id}") from e

    def all(self) -> Mapping[str, ValidationRule]:
        return dict(self._rules)

    # --------------------------------------------------------------------------
    # Execution API
    # --------------------------------------------------------------------------
    def validate(
        self,
        rule_id: str,
        value: Any,
        *,
        context: ValidationContext | None = None,
    ) -> ValidationResult:
        rule = self.get(rule_id)
        return rule(value, context=context)


# ╭────────────────────────────────────────────────────────────────────────────╮
# │ Factory for creating safe registry instances                               │
# ╰────────────────────────────────────────────────────────────────────────────╯
class ValidatorRegistryFactory:
    """
    Factory for producing sealed ValidatorRegistry instances.

    Clean Architecture:
        • Application bootstrap calls ValidatorRegistryFactory.create_default()
        • Tests can create custom registries safely
    """

    @staticmethod
    def create_default(
        default_rules: Mapping[str, ValidationRule],
    ) -> ValidatorRegistry:
        reg = ValidatorRegistry()
        reg.register_many(default_rules)
        reg.seal()
        return reg
