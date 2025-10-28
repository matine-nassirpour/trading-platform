"""
Quantum Core — Integration Tests: Failure Resilience and Error Handling
────────────────────────────────────────────────────────────────────────
Validate the robustness of the configuration system against corrupted
files, invalid environment values, internal state corruption, and concurrency.
"""

from __future__ import annotations

import os
import threading
from pathlib import Path

import pytest

from quantum.platform.config.models.core import CoreSettings
from quantum.platform.config.providers.env_loader import load_env
from quantum.platform.config.runtime.manager import ConfigManager
from quantum.platform.config.runtime.state import ConfigState


# ╭────────────────────────────────────────────────────────────────────────────╮
# │ Missing or unreadable .env files                                           │
# ╰────────────────────────────────────────────────────────────────────────────╯
@pytest.mark.integration
def test_load_env_missing_or_empty_file(tmp_workspace, iso_env):
    """
    load_env() must safely handle missing or empty .env files without crashing.
    """
    root = tmp_workspace["root"]

    # Missing file
    missing = root / "no_file.env"
    result_missing = load_env(root=missing.parent, apply=True)
    assert isinstance(result_missing, dict)

    # Empty file
    empty = root / ".env"
    empty.write_text("", encoding="utf-8")
    result_empty = load_env(root=root, apply=True)
    assert isinstance(result_empty, dict)
    assert result_empty == {} or "QUANTUM_ENV" in result_empty

    # Ensure state is sane
    snap = ConfigState.instance().snapshot()
    assert isinstance(snap["env_cache"], dict)


@pytest.mark.integration
def test_load_env_with_corrupted_bytes(tmp_workspace, iso_env):
    """
    Corrupted .env (non-UTF8 bytes) should raise a predictable decoding error,
    not a crash or inconsistent state.
    """
    env_path = tmp_workspace["root"] / ".env"
    env_path.write_bytes(b"\xff\xfeINVALID_ENV=\x80")

    with pytest.raises(UnicodeDecodeError):
        load_env(root=tmp_workspace["root"], apply=True)


# ╭────────────────────────────────────────────────────────────────────────────╮
# │ Invalid environment values                                                 │
# ╰────────────────────────────────────────────────────────────────────────────╯
@pytest.mark.integration
def test_invalid_env_values_fallback_to_default(tmp_workspace, iso_env):
    """
    Invalid environment values should gracefully fallback to defaults.
    """
    env_path = tmp_workspace["root"] / ".env"
    env_path.write_text("QUANTUM_METRICS_PORT=not_a_number\n", encoding="utf-8")

    cfg = ConfigManager.load(root=tmp_workspace["root"], apply=True)
    default_port = CoreSettings().quantum_metrics_port
    assert cfg.quantum_metrics_port == default_port


# ╭────────────────────────────────────────────────────────────────────────────╮
# │ Snapshot resilience under corruption                                       │
# ╰────────────────────────────────────────────────────────────────────────────╯
@pytest.mark.integration
def test_snapshot_survives_internal_corruption(tmp_workspace, iso_env):
    """
    Even if internal state is corrupted, snapshot() must remain callable and
    return a stable dict structure.
    """
    state = ConfigState.instance()
    state.reset()
    state.update(
        base_dir=tmp_workspace["root"], loaded_pid=os.getpid(), env_cache={"A": "B"}
    )

    # Corrupt state
    state._env_cache = None  # type: ignore
    state._base_dir = None
    state._loaded_pid = None

    snap = state.snapshot()
    assert isinstance(snap["env_cache"], dict)
    assert "loaded_pid" in snap


# ╭────────────────────────────────────────────────────────────────────────────╮
# │ Thread safety during raised exceptions                                     │
# ╰────────────────────────────────────────────────────────────────────────────╯
@pytest.mark.integration
def test_concurrent_access_exception_does_not_deadlock(tmp_workspace, iso_env):
    """
    Exceptions inside access() must not corrupt or block internal lock.
    """
    state = ConfigState.instance()
    state.reset()
    state.update(
        base_dir=tmp_workspace["root"], env_cache={"CNT": "0"}, loaded_pid=os.getpid()
    )

    def failing_op():
        def op():
            raise RuntimeError("simulated failure")

        with pytest.raises(RuntimeError):
            state.access(op)

    threads = [threading.Thread(target=failing_op) for _ in range(10)]
    for t in threads:
        t.start()
    for t in threads:
        t.join(timeout=3)

    # State must remain intact and lock released
    snap = state.snapshot()
    assert isinstance(snap["env_cache"], dict)
    assert snap["loaded_pid"] == os.getpid()


# ╭────────────────────────────────────────────────────────────────────────────╮
# │ Cache invalidation and reset behavior                                      │
# ╰────────────────────────────────────────────────────────────────────────────╯
@pytest.mark.integration
def test_clear_caches_restores_clean_state(tmp_workspace, iso_env):
    """
    ConfigManager.clear_caches() must clear LRU cache and reset ConfigState.
    """
    env_path = tmp_workspace["root"] / ".env"
    env_path.write_text("QUANTUM_APP_NAME=testapp\n", encoding="utf-8")
    ConfigManager.load(root=tmp_workspace["root"], apply=True)

    ConfigManager.clear_caches()
    state = ConfigState.instance().snapshot()
    assert state["env_cache"] == {}
    assert state["base_dir"] is None
    assert state["loaded_pid"] is None


# ╭────────────────────────────────────────────────────────────────────────────╮
# │ Resilience of ConfigManager.snapshot()                                     │
# ╰────────────────────────────────────────────────────────────────────────────╯
@pytest.mark.integration
def test_manager_snapshot_remains_stable_even_with_partial_env(tmp_workspace, iso_env):
    """
    ConfigManager.snapshot() must not raise even if environment is incomplete.
    """
    env_path = tmp_workspace["root"] / ".env"
    env_path.write_text("QUANTUM_APP_NAME=x\nQUANTUM_ENV=prod\n", encoding="utf-8")

    snap = ConfigManager.snapshot()
    assert isinstance(snap, dict)
    for key in ("app", "version", "env", "trace_exporter", "metrics_port"):
        assert key in snap


# ╭────────────────────────────────────────────────────────────────────────────╮
# │ Fallback for missing base_dir and default env                              │
# ╰────────────────────────────────────────────────────────────────────────────╯
@pytest.mark.integration
def test_load_env_fallback_to_cwd_when_no_root(tmp_path, iso_env):
    """
    When root and env_file are None, load_env() must fall back to cwd safely.
    """
    result = load_env(root=None, env_file=None, apply=False)
    assert isinstance(result, dict)
    base_dir = ConfigState.instance().snapshot()["base_dir"]
    assert base_dir is None or Path(base_dir) == Path.cwd()
