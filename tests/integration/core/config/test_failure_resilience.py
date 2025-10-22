from __future__ import annotations

import os
import threading
from pathlib import Path

import pytest

from quantum.core.config.providers.env_loader import load_env
from quantum.core.config.runtime.manager import ConfigManager
from quantum.core.config.runtime.state import ConfigState


# ╭─────────────────────────────────────────────────────────────────────────────╮
# │ 1. Handling of missing or unreadable .env files                             │
# ╰─────────────────────────────────────────────────────────────────────────────╯
@pytest.mark.integration
def test_load_env_missing_file_does_not_crash(tmp_workspace, iso_env):
    """
    load_env() must safely handle a missing or empty .env file.
    """
    missing = tmp_workspace["root"] / "no_file.env"
    result = load_env(root=missing.parent, apply=True)
    assert isinstance(result, dict)
    assert "QUANTUM_ENV" in result or result == {}


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


# ╭─────────────────────────────────────────────────────────────────────────────╮
# │ 2. Resilience to invalid environment values                                 │
# ╰─────────────────────────────────────────────────────────────────────────────╯
@pytest.mark.integration
def test_invalid_env_values_are_tolerated_with_default(tmp_workspace, iso_env):
    """
    Invalid environment values should fall back to default without crashing.
    """
    env_path = tmp_workspace["root"] / ".env"
    env_path.write_text("QUANTUM_METRICS_PORT=not_a_number\n", encoding="utf-8")

    cfg = ConfigManager.load(root=tmp_workspace["root"], apply=True)
    assert isinstance(cfg.quantum_metrics_port, int)
    assert cfg.quantum_metrics_port == 0  # fallback to default


# ╭─────────────────────────────────────────────────────────────────────────────╮
# │ 3. Snapshot resilience under internal corruption                            │
# ╰─────────────────────────────────────────────────────────────────────────────╯
@pytest.mark.integration
def test_snapshot_survives_internal_corruption(tmp_workspace, iso_env):
    """
    Even if internal state is corrupted, snapshot() must remain callable.
    """
    state = ConfigState.instance()
    state.reset()
    state.update(
        base_dir=tmp_workspace["root"], loaded_pid=os.getpid(), env_cache={"A": "B"}
    )

    # Simulate internal corruption
    state._env_cache = None  # type: ignore
    state._base_dir = None

    # snapshot must still return a consistent structure
    snap = state.snapshot()
    assert "env_cache" in snap
    assert isinstance(snap["env_cache"], dict)
    assert "loaded_pid" in snap


# ╭─────────────────────────────────────────────────────────────────────────────╮
# │ 4. Thread safety during raised exceptions                                   │
# ╰─────────────────────────────────────────────────────────────────────────────╯
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


# ╭─────────────────────────────────────────────────────────────────────────────╮
# │ 5. Cache invalidation and reset behavior                                    │
# ╰─────────────────────────────────────────────────────────────────────────────╯
@pytest.mark.integration
def test_clear_caches_restores_clean_state(tmp_workspace, iso_env):
    """
    ConfigManager.clear_caches() must clear lru_cache and reset ConfigState.
    """
    # Pre-load configuration
    env_path = tmp_workspace["root"] / ".env"
    env_path.write_text("QUANTUM_APP_NAME=testapp\n", encoding="utf-8")
    ConfigManager.load(root=tmp_workspace["root"], apply=True)

    ConfigManager.clear_caches()
    state = ConfigState.instance()
    snap = state.snapshot()

    assert snap["env_cache"] == {}
    assert snap["base_dir"] is None
    assert snap["loaded_pid"] is None


# ╭─────────────────────────────────────────────────────────────────────────────╮
# │ 6. Resilience of ConfigManager.snapshot()                                   │
# ╰─────────────────────────────────────────────────────────────────────────────╯
@pytest.mark.integration
def test_manager_snapshot_remains_stable_even_with_partial_env(tmp_workspace, iso_env):
    """
    ConfigManager.snapshot() must not raise even if environment is incomplete.
    """
    env_path = tmp_workspace["root"] / ".env"
    env_path.write_text("QUANTUM_APP_NAME=x\nQUANTUM_ENV=prod\n", encoding="utf-8")

    try:
        snap = ConfigManager.snapshot()
        assert isinstance(snap, dict)
        for key in ("app", "version", "env", "trace_exporter", "metrics_port"):
            assert key in snap
    except Exception as e:  # pragma: no cover
        pytest.fail(f"ConfigManager.snapshot() failed unexpectedly: {e!r}")


# ╭─────────────────────────────────────────────────────────────────────────────╮
# │ 7. Fallback for missing base_dir and default env                            │
# ╰─────────────────────────────────────────────────────────────────────────────╯
@pytest.mark.integration
def test_load_env_fallback_to_cwd_when_no_root(tmp_path, iso_env):
    """
    When root and env_file are None, load_env() must fall back to cwd safely.
    """
    cwd = Path.cwd()
    result = load_env(root=None, env_file=None, apply=False)
    assert isinstance(result, dict)
    assert ConfigState.instance().snapshot()["base_dir"] in (str(cwd), None)
