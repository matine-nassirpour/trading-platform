from __future__ import annotations

import os
from collections.abc import Callable
from pathlib import Path
from typing import Any, cast

import pytest

_NumberLike = float | int | str | bytes


def _gauge_value(g: Any) -> float:
    maybe_get = getattr(getattr(g, "_value", None), "get", None)
    if not callable(maybe_get):
        return -1.0
    try:
        return float(cast(Callable[[], _NumberLike], maybe_get)())
    except Exception:
        return -1.0


def _init_then_assert_then_shutdown(assert_fn) -> None:
    """Init → assert → shutdown (always cleanly, even on failure)."""
    from quantum.infrastructure.observability.init_observability import (
        init_observability,
        shutdown_observability,
    )

    init_observability(force=True)
    try:
        assert_fn()
    finally:
        shutdown_observability(
            close_logging=True,
            shutdown_tracing=True,
            reset_state=True,
            set_gauges_down=True,
        )


@pytest.mark.usefixtures("no_rate_limit_no_sampling")
class TestPersistenceProbe:
    def test_no_persistent_sinks_sets_logging_sink_up_0(self, tmp_workspace):
        """Without QUANTUM_LOG_DIR or QUANTUM_AUDIT_DIR → logging_sink_up == 0."""
        from quantum.infrastructure.observability.metrics import health as m

        os.environ.pop("QUANTUM_LOG_DIR", None)
        os.environ.pop("QUANTUM_AUDIT_DIR", None)

        def _assert():
            assert _gauge_value(m.pipeline_logging_ok) in (0.0, 1.0)  # init can succeed
            assert _gauge_value(m.logging_sink_up) == 0.0

        _init_then_assert_then_shutdown(_assert)

    def test_log_dir_only_sets_logging_sink_up_1(self, tmp_workspace):
        """With QUANTUM_LOG_DIR writable (alone) → logging_sink_up == 1."""
        from quantum.infrastructure.observability.metrics import health as m

        os.environ["QUANTUM_LOG_DIR"] = str(tmp_workspace["logs"])
        os.environ.pop("QUANTUM_AUDIT_DIR", None)

        def _assert():
            assert _gauge_value(m.logging_sink_up) == 1.0

        _init_then_assert_then_shutdown(_assert)

    def test_audit_dir_only_sets_logging_sink_up_1(self, tmp_workspace):
        """With QUANTUM_AUDIT_DIR writable (alone) → logging_sink_up == 1."""
        from quantum.infrastructure.observability.metrics import health as m

        os.environ["QUANTUM_AUDIT_DIR"] = str(tmp_workspace["audit"])
        os.environ.pop("QUANTUM_LOG_DIR", None)

        def _assert():
            assert _gauge_value(m.logging_sink_up) == 1.0

        _init_then_assert_then_shutdown(_assert)

    def test_both_dirs_sets_logging_sink_up_1(self, tmp_workspace):
        """With both directories valid → logging_sink_up == 1."""
        from quantum.infrastructure.observability.metrics import health as m

        os.environ["QUANTUM_LOG_DIR"] = str(tmp_workspace["logs"])
        os.environ["QUANTUM_AUDIT_DIR"] = str(tmp_workspace["audit"])

        def _assert():
            assert _gauge_value(m.logging_sink_up) == 1.0

        _init_then_assert_then_shutdown(_assert)

    def test_invalid_log_dir_and_no_audit_sets_0(self, tmp_workspace, tmp_path):
        """
        QUANTUM_LOG_DIR points to a FILE (os.makedirs fails) and no auditing → logging_sink_up == 0.
        This simulates a reliable cross-platform 'unwritable'.
        """
        from quantum.infrastructure.observability.metrics import health as m

        bogus = Path(tmp_path) / "not_a_dir.jsonl"
        bogus.write_text("x", encoding="utf-8")
        os.environ["QUANTUM_LOG_DIR"] = str(bogus)  # <-- pas un dossier
        os.environ.pop("QUANTUM_AUDIT_DIR", None)

        def _assert():
            assert _gauge_value(m.logging_sink_up) == 0.0

        _init_then_assert_then_shutdown(_assert)

    def test_invalid_log_dir_but_valid_audit_sets_1(self, tmp_workspace, tmp_path):
        """Invalid log dir but valid audit dir → at least one writable sink → logging_sink_up == 1."""
        from quantum.infrastructure.observability.metrics import health as m

        bogus = Path(tmp_path) / "not_a_dir.jsonl"
        bogus.write_text("x", encoding="utf-8")
        os.environ["QUANTUM_LOG_DIR"] = str(bogus)
        os.environ["QUANTUM_AUDIT_DIR"] = str(tmp_workspace["audit"])

        def _assert():
            assert _gauge_value(m.logging_sink_up) == 1.0

        _init_then_assert_then_shutdown(_assert)

    def test_deep_probe_enabled_keeps_logging_sink_up_1(self, tmp_workspace):
        """
        With QUANTUM_LOG_DIR + QUANTUM_LOG_DEEP_PROBE=1 → the write/read/cleanup probe passes,
        logging_sink_up == 1. (We don't care about the presence of __probe__ because the code is partially clean.)
        """
        from quantum.infrastructure.observability.metrics import health as m

        os.environ["QUANTUM_LOG_DIR"] = str(tmp_workspace["logs"])
        os.environ.pop("QUANTUM_AUDIT_DIR", None)
        os.environ["QUANTUM_LOG_DEEP_PROBE"] = "1"

        def _assert():
            assert _gauge_value(m.logging_sink_up) == 1.0

        _init_then_assert_then_shutdown(_assert)
        # Cleaning approx.
        os.environ.pop("QUANTUM_LOG_DEEP_PROBE", None)
