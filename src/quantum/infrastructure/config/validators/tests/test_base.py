import pytest

from quantum.infrastructure.config.validators.base import (
    ValidationContext,
    ValidationResult,
    ValidationRule,
)

# ╭─────────────────────────────────────────────────────────────────────────────╮
# │ ValidationResult                                                            │
# ╰─────────────────────────────────────────────────────────────────────────────╯


def test_validation_result_success_ok_type():
    result = ValidationResult(ok=True, message=None, value="ok", rule="platform.rule")
    value = result.raise_if_failed()

    assert result.ok is True
    assert value == "ok"
    assert result.rule == "platform.rule"


def test_validation_result_failure_raises():
    result = ValidationResult(
        ok=False, message="error", value=None, rule="platform.fail"
    )

    with pytest.raises(ValueError, match="error"):
        result.raise_if_failed()


# ╭─────────────────────────────────────────────────────────────────────────────╮
# │ ValidationContext                                                           │
# ╰─────────────────────────────────────────────────────────────────────────────╯


def test_context_describe_default():
    ctx = ValidationContext()
    desc = ctx.describe()

    assert "anonymous" in desc
    assert "field=" not in desc


def test_context_describe_full():
    ctx = ValidationContext(model_name="CoreSettings", field_name="quantum_env")
    s = ctx.describe()
    assert "model=CoreSettings" in s
    assert "field=quantum_env" in s


# ╭─────────────────────────────────────────────────────────────────────────────╮
# │ ValidationRule — via Dummy subclass                                         │
# ╰─────────────────────────────────────────────────────────────────────────────╯


class DummyRule(ValidationRule):
    def __init__(self):
        super().__init__("dummy.rule", "Dummy validator for testing")

    def __call__(self, value, *, context=None):
        if not value:
            return self.failure("empty")
        return self.success(value.upper())


def test_validation_rule_success_and_failure_helpers():
    rule = DummyRule()
    ok = rule.success("ok")
    fail = rule.failure("bad")

    assert ok.ok is True and fail.ok is False
    assert isinstance(ok, ValidationResult)
    assert isinstance(fail, ValidationResult)


def test_validation_rule_invocation_returns_result():
    rule = DummyRule()
    result = rule("abc")

    assert isinstance(result, ValidationResult)
    assert result.ok
    assert result.value == "ABC"


def test_validation_rule_failure_path():
    rule = DummyRule()
    res = rule("")

    assert not res.ok
    assert "empty" in res.message
