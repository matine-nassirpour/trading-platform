import os
import threading
import time
from pathlib import Path

import pytest

from quantum.core.config.providers.env_loader import load_env
from quantum.core.config.runtime.state import ConfigState


@pytest.mark.integration
def test_singleton_identity_across_imports():
    """
    The ConfigState must always return the same instance across imports.
    """
    state1 = ConfigState.instance()
    state2 = ConfigState.instance()
    assert state1 is state2
    assert id(state1) == id(state2)


@pytest.mark.integration
def test_snapshot_and_reset_cycle(tmp_path: Path, iso_env):
    """
    snapshot() reflects env cache after load_env(), and reset() clears pid/cache.
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

    state.update(env_cache={"X": "1"})
    assert state.snapshot()["env_cache"] == {"X": "1"}


@pytest.mark.integration
def test_thread_safety_during_concurrent_access(tmp_path: Path, iso_env):
    """
    Concurrent readers/writers must not corrupt the cache; last write wins.
    """
    (tmp_path / ".env").write_text("FOO=base\n", encoding="utf-8")
    load_env(root=tmp_path, apply=True)
    state = ConfigState.instance()

    def writer(i: int):
        state.update(env_cache={"FOO": f"value_{i}"})

    def reader(results: list[str | None]):
        snap = state.snapshot()
        results.append(snap["env_cache"].get("FOO"))

    threads = []
    reads: list[str | None] = []
    for i in range(10):
        threads.append(threading.Thread(target=writer, args=(i,)))
        threads.append(threading.Thread(target=reader, args=(reads,)))

    for t in threads:
        t.start()
    for t in threads:
        t.join()

    snap = state.snapshot()
    assert isinstance(snap["env_cache"], dict)
    assert "FOO" in snap["env_cache"]
    assert all((v is None) or isinstance(v, str) for v in reads)


@pytest.mark.integration
def test_pid_invalidation(tmp_path: Path, iso_env):
    """
    Cache validity must depend on current PID; mismatch invalidates cache.
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


@pytest.mark.integration
def test_multiple_resets_are_idempotent():
    """
    reset() is safe to call repeatedly; state remains consistent.
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


@pytest.mark.integration
def test_env_cache_consistency_during_updates(tmp_path: Path, iso_env):
    """
    Updates to env cache are atomic; final snapshot reflects the last write.
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
    t.join()

    snap = state.snapshot()
    assert "FOO" in snap["env_cache"]
    assert snap["env_cache"]["FOO"].startswith("v")
