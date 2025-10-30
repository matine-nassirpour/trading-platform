"""
Quantum Core — Integration Tests: Runtime State
────────────────────────────────────────────────
Validate thread safety, cache consistency, and lifecycle invariants
of the ConfigState singleton used as the runtime configuration anchor.
"""

import os
import threading
import time
from pathlib import Path

import pytest

from quantum.infrastructure.config.providers.env_loader import load_env
from quantum.infrastructure.config.runtime.state import ConfigState


# ╭────────────────────────────────────────────────────────────────────────────╮
# │ Singleton identity and lifecycle invariants                                │
# ╰────────────────────────────────────────────────────────────────────────────╯
@pytest.mark.integration
def test_singleton_identity_across_imports():
    """
    ConfigState must always return the same instance across imports
    """
    state1 = ConfigState.instance()
    state2 = ConfigState.instance()
    assert state1 is state2
    assert id(state1) == id(state2)
    assert callable(state1.snapshot)


@pytest.mark.integration
def test_snapshot_and_reset_cycle(tmp_path: Path, iso_env):
    """
    snapshot() reflects env cache after load_env(), and reset() clears pid/cache
    """
    (tmp_path / ".env").write_text("FOO=bar\n", encoding="utf-8")
    _ = load_env(root=tmp_path, apply=True)
    state = ConfigState.instance()

    snap_before = state.snapshot()
    assert snap_before["loaded_pid"] == os.getpid()
    assert snap_before["env_cache"].get("FOO") == "bar"

    state.reset()
    snap_after = state.snapshot()
    assert snap_after["loaded_pid"] is None
    assert snap_after["env_cache"] == {}
    assert not state.has_valid_cache()

    state.update(env_cache={"X": "1"}, loaded_pid=os.getpid())
    assert state.has_valid_cache()
    assert state.snapshot()["env_cache"] == {"X": "1"}


# ╭────────────────────────────────────────────────────────────────────────────╮
# │ Concurrency and thread safety                                              │
# ╰────────────────────────────────────────────────────────────────────────────╯
@pytest.mark.integration
def test_thread_safety_during_concurrent_access(tmp_path: Path, iso_env):
    """
    Concurrent readers/writers must not corrupt the cache; last write wins
    """
    (tmp_path / ".env").write_text("FOO=base\n", encoding="utf-8")
    load_env(root=tmp_path, apply=True)
    state = ConfigState.instance()

    def writer(i: int):
        state.update(env_cache={"FOO": f"value_{i}"})

    def reader(results: list[str | None]):
        results.append(state.snapshot()["env_cache"].get("FOO"))

    threads = []
    reads: list[str | None] = []
    for i in range(10):
        threads += [
            threading.Thread(target=writer, args=(i,)),
            threading.Thread(target=reader, args=(reads,)),
        ]

    for t in threads:
        t.start()
    for t in threads:
        t.join(timeout=2)

    assert all(not t.is_alive() for t in threads)
    snap = state.snapshot()
    assert isinstance(snap["env_cache"], dict)
    assert "FOO" in snap["env_cache"]
    assert snap["env_cache"]["FOO"].startswith("value_")
    assert all(v is None or isinstance(v, str) for v in reads)


# ╭────────────────────────────────────────────────────────────────────────────╮
# │ PID validation and cache invalidation                                      │
# ╰────────────────────────────────────────────────────────────────────────────╯
@pytest.mark.integration
def test_pid_invalidation(tmp_path: Path, iso_env):
    """
    Cache validity must depend on current PID; mismatch invalidates cache
    """
    (tmp_path / ".env").write_text("A=1\n", encoding="utf-8")
    load_env(root=tmp_path)
    state = ConfigState.instance()

    pid_before = state.snapshot()["loaded_pid"]
    assert pid_before == os.getpid()
    assert state.has_valid_cache()

    state.update(loaded_pid=pid_before + 1)
    assert not state.has_valid_cache()

    state.update(loaded_pid=os.getpid())
    assert state.has_valid_cache()
    assert state.snapshot()["loaded_pid"] == os.getpid()


# ╭────────────────────────────────────────────────────────────────────────────╮
# │ Reset idempotence and safe reentrancy                                      │
# ╰────────────────────────────────────────────────────────────────────────────╯
@pytest.mark.integration
def test_multiple_resets_are_idempotent():
    """
    reset() is safe to call repeatedly; state remains consistent
    """
    state = ConfigState.instance()
    state.update(env_cache={"X": "1"}, loaded_pid=os.getpid())
    assert state.has_valid_cache()

    for _ in range(5):
        state.reset()
        assert not state.has_valid_cache()
        state.update(env_cache={"X": "1"}, loaded_pid=os.getpid())
        assert state.has_valid_cache()

    state.reset()
    assert not state.has_valid_cache()
    assert id(state) == id(ConfigState.instance())


# ╭────────────────────────────────────────────────────────────────────────────╮
# │ Atomicity and coherence of updates                                         │
# ╰────────────────────────────────────────────────────────────────────────────╯
@pytest.mark.integration
def test_env_cache_consistency_during_updates(tmp_path: Path, iso_env):
    """
    Updates to env cache are atomic; final snapshot reflects the last write
    """
    (tmp_path / ".env").write_text("FOO=bar\n", encoding="utf-8")
    load_env(root=tmp_path, apply=True)
    state = ConfigState.instance()

    state.update(env_cache={"FOO": "initial"})

    def concurrent_update():
        for i in range(5):
            state.update(env_cache={"FOO": f"v{i}"})
            time.sleep(0.002)

    t = threading.Thread(target=concurrent_update)
    t.start()
    for _ in range(3):
        state.update(env_cache={"FOO": "main"})
    t.join()

    snap = state.snapshot()
    assert "FOO" in snap["env_cache"]
    assert snap["env_cache"]["FOO"].startswith("v")
    assert isinstance(snap["env_cache"]["FOO"], str)
