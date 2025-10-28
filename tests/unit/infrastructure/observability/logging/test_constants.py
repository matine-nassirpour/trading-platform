from __future__ import annotations

import pytest

from quantum.infrastructure.observability.logging.constants import (
    get_audit_allowlist,
    is_audit_event,
)


@pytest.mark.usefixtures("iso_env")
class TestAuditConstants:
    def test_baseline_allowlist_contains_core_events(self):
        """
        Given the default configuration
        When reading the audit allowlist
        Then platform baseline events must be present
        """
        allow = get_audit_allowlist()
        required = {
            "order_submit",
            "order_ack",
            "order_fill",
            "order_reject",
            "killswitch_trigger",
            "reconciliation",
        }
        missing = required.difference(allow)
        assert not missing, f"missing baseline events: {sorted(missing)}"

    def test_env_expansion_and_version_suffix_are_normalized(self, monkeypatch):
        """
        Given custom events from environment with version suffixes and spaces
        When reading the allowlist
        Then custom names are normalized (version-agnostic) and merged with baseline
        And is_audit_event() must accept any version suffix for allowed names
        """
        # Arrange
        monkeypatch.setenv(
            "QUANTUM_AUDIT_EVENTS", " custom_event_v2 ,   extra_v10  ,order_submit_v3"
        )

        # Act
        allow = get_audit_allowlist()

        # Assert: custom names normalized and baseline preserved
        assert "custom_event" in allow
        assert "extra" in allow
        assert "order_submit" in allow  # baseline still present

        # Assert: version-agnostic checks
        assert is_audit_event("custom_event_v9")
        assert is_audit_event("extra_v1")
        assert is_audit_event("order_submit_v100")

    @pytest.mark.parametrize(
        "env_value",
        [
            "valid_name,Invalid-Name",
            "bad*chars,ok",
            "with space,ok",
        ],
    )
    def test_invalid_name_in_env_raises_valueerror(self, monkeypatch, env_value: str):
        """
        Given invalid names provided via environment
        When reading the allowlist
        Then a ValueError is raised
        """
        # Arrange
        monkeypatch.setenv("QUANTUM_AUDIT_EVENTS", env_value)

        # Act / Assert
        with pytest.raises(ValueError):
            _ = get_audit_allowlist()

    def test_is_audit_event_false_for_unknown(self, monkeypatch):
        """
        Given an empty extension list
        When querying unknown or malformed event names
        Then is_audit_event returns False
        """
        # Arrange
        monkeypatch.setenv("QUANTUM_AUDIT_EVENTS", "")

        # Act / Assert
        assert not is_audit_event("totally_unknown_v1")
        assert not is_audit_event("bad*chars")

    @pytest.mark.parametrize(
        ("env_value", "query", "expected"),
        [
            ("custom_v1", "custom_v2", True),
            ("custom_v1,another_v3", "another_v99", True),
            ("", "order_ack_v1", True),  # baseline must still work
            ("", "unknown_v1", False),
        ],
    )
    def test_is_audit_event_version_agnostic_and_baseline(
        self, monkeypatch, env_value: str, query: str, expected: bool
    ):
        """
        Given an environment-provided CSV and a query with any version suffix
        When calling is_audit_event
        Then it must be version-agnostic and include baseline entries
        """
        # Arrange
        monkeypatch.setenv("QUANTUM_AUDIT_EVENTS", env_value)

        # Act
        result = is_audit_event(query)

        # Assert
        assert result is expected, f"expected {expected} for query={query!r}"
