from __future__ import annotations

import os

import pytest

from quantum.infrastructure.observability.logging.constants import (
    get_audit_allowlist,
    is_audit_event,
)


@pytest.mark.usefixtures("iso_env")
class TestAuditConstants:
    def test_baseline_allowlist_contains_core_events(self):
        allow = get_audit_allowlist()
        for k in {
            "order_submit",
            "order_ack",
            "order_fill",
            "order_reject",
            "killswitch_trigger",
            "reconciliation",
        }:
            assert k in allow

    def test_env_expansion_and_version_suffix_are_normalized(self, monkeypatch):
        # Ajoute des entrées via l'env, avec suffixes et espaces
        os.environ["QUANTUM_AUDIT_EVENTS"] = (
            " custom_event_v2 ,   extra_v10  ,order_submit_v3"
        )
        allow = get_audit_allowlist()
        assert "custom_event" in allow
        assert "extra" in allow
        # baseline toujours présent
        assert "order_submit" in allow
        # vérifie la détection version-agnostique
        assert is_audit_event("custom_event_v9")
        assert is_audit_event("extra_v1")
        assert is_audit_event("order_submit_v100")

    def test_invalid_name_in_env_raises_valueerror(self):
        os.environ["QUANTUM_AUDIT_EVENTS"] = "valid_name,Invalid-Name"
        with pytest.raises(ValueError):
            _ = get_audit_allowlist()

    def test_is_audit_event_false_for_unknown(self):
        os.environ["QUANTUM_AUDIT_EVENTS"] = ""
        assert not is_audit_event("totally_unknown_v1")
        assert not is_audit_event("bad*chars")
