"""
Quantum Core — Integration Tests: Validator Registry and Rule Execution
────────────────────────────────────────────────────────────────────────
Validate the behavior of the central ValidatorRegistry, its rule lifecycle,
default registration, context propagation, and ValidationResult semantics.
"""

from __future__ import annotations

from typing import Any

import pytest

from quantum.core.config.validators.base import (
    ValidationContext,
    ValidationResult,
    ValidationRule,
)
from quantum.core.config.validators.registry import ValidatorRegistry


# ╭─────────────────────────────────────────────────────────────────────────────╮
# │ Utility: Dummy validation rule for controlled testing                       │
# ╰─────────────────────────────────────────────────────────────────────────────╯
class DummyRule(ValidationRule):
    """Simple rule that succeeds or fails depending on value type."""

    def __init__(self, should_pass: bool = True):
        super().__init__(
            rule_id="dummy.pass" if should_pass else "dummy.fail",
            description="Test rule that conditionally passes or fails.",
        )
        self.should_pass = should_pass

    def __call__(
        self, value: Any, *, context: ValidationContext | None = None
    ) -> ValidationResult:
        if self.should_pass:
            return self.success(value)
        return self.failure(f"Rejected value: {value!r}")


# ╭─────────────────────────────────────────────────────────────────────────────╮
# │ Registry lifecycle and isolation                                            │
# ╰─────────────────────────────────────────────────────────────────────────────╯
@pytest.mark.integration
def test_clear_and_register_isolated(iso_env):
    """
    Clearing the registry must remove all prior rules and allow clean re-registration
    """
    ValidatorRegistry.clear_registry()
    assert ValidatorRegistry.all() == {}

    r1 = DummyRule()
    ValidatorRegistry.register(r1)
    assert "dummy.pass" in ValidatorRegistry.all()

    ValidatorRegistry.clear_registry()
    assert ValidatorRegistry.all() == {}


# ╭─────────────────────────────────────────────────────────────────────────────╮
# │ Duplicate registration handling                                             │
# ╰─────────────────────────────────────────────────────────────────────────────╯
@pytest.mark.integration
def test_register_duplicate_rule_raises_valueerror(iso_env):
    """
    Registering a rule with an existing ID must raise ValueError
    """
    ValidatorRegistry.clear_registry()
    ValidatorRegistry.register(DummyRule())

    with pytest.raises(ValueError):
        ValidatorRegistry.register(DummyRule())  # same rule_id


# ╭─────────────────────────────────────────────────────────────────────────────╮
# │ Lookup and retrieval consistency                                            │
# ╰─────────────────────────────────────────────────────────────────────────────╯
@pytest.mark.integration
def test_get_and_all_reflect_current_registry(iso_env):
    """
    The registry must expose the same rule objects via get() and all()
    """
    ValidatorRegistry.clear_registry()
    rule = DummyRule()
    ValidatorRegistry.register(rule)

    retrieved = ValidatorRegistry.get("dummy.pass")
    assert retrieved is rule

    snapshot = ValidatorRegistry.all()
    assert snapshot["dummy.pass"] is rule


@pytest.mark.integration
def test_get_unknown_rule_raises_keyerror(iso_env):
    """
    Retrieving a non-existent validator must raise KeyError
    """
    ValidatorRegistry.clear_registry()
    with pytest.raises(KeyError):
        ValidatorRegistry.get("unknown.rule")


# ╭─────────────────────────────────────────────────────────────────────────────╮
# │ ValidationResult contract and rule execution                                │
# ╰─────────────────────────────────────────────────────────────────────────────╯
@pytest.mark.integration
def test_validationresult_success_and_failure_semantics(iso_env):
    """
    ValidationResult must encapsulate correctness, message, and raise_if_failed()
    """
    ok = ValidationResult(ok=True, message=None, value="x", rule="demo")
    assert ok.raise_if_failed() == "x"

    fail = ValidationResult(ok=False, message="bad", value=None, rule="demo")
    with pytest.raises(ValueError):
        fail.raise_if_failed()


@pytest.mark.integration
def test_rule_execution_success_and_failure(iso_env):
    """
    The registry must execute registered rules and return consistent ValidationResult objects
    """
    ValidatorRegistry.clear_registry()
    ok_rule = DummyRule(True)
    bad_rule = DummyRule(False)
    ValidatorRegistry.register(ok_rule)
    ValidatorRegistry.register(bad_rule)

    # Success case
    result_ok = ValidatorRegistry.validate("dummy.pass", value="A")
    assert result_ok.ok is True
    assert result_ok.rule == "dummy.pass"
    assert result_ok.message is None

    # Failure case
    result_fail = ValidatorRegistry.validate("dummy.fail", value="Z")
    assert result_fail.ok is False
    assert "Rejected" in result_fail.message


# ╭─────────────────────────────────────────────────────────────────────────────╮
# │ Context propagation and introspection                                       │
# ╰─────────────────────────────────────────────────────────────────────────────╯
@pytest.mark.integration
def test_validationcontext_description_and_usage(iso_env):
    """
    ValidationContext must render a readable descriptor and propagate correctly
    """
    captured_ctx: list[ValidationContext] = []

    class CaptureRule(ValidationRule):
        def __init__(self):
            super().__init__("capture.ctx", "Captures context")

        def __call__(
            self, value: Any, *, context: ValidationContext | None = None
        ) -> ValidationResult:
            if context:
                captured_ctx.append(context)
            return self.success(value)

    ValidatorRegistry.clear_registry()
    ValidatorRegistry.register(CaptureRule())

    ctx = ValidationContext(field_name="quantum_env", model_name="CoreSettings")
    ValidatorRegistry.validate("capture.ctx", "dev", context=ctx)

    assert captured_ctx and captured_ctx[0].field_name == "quantum_env"
    assert "model=CoreSettings" in captured_ctx[0].describe()


# ╭─────────────────────────────────────────────────────────────────────────────╮
# │ Default rules bootstrapping                                                 │
# ╰─────────────────────────────────────────────────────────────────────────────╯
@pytest.mark.integration
def test_register_defaults_bootstraps_ruleset(iso_env):
    """
    The registry must initialize with all built-in validators declared in register_defaults()
    """
    ValidatorRegistry.clear_registry()
    ValidatorRegistry.register_defaults()

    defaults = ValidatorRegistry.all()
    expected_prefixes = (
        "core.runtime.environment",
        "core.logging.log_level",
        "core.logging.timezone",
        "core.tracing.otlp_protocol",
        "core.tracing.compression",
    )

    for prefix in expected_prefixes:
        assert prefix in defaults, f"Missing default validator: {prefix}"
