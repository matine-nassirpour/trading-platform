"""
Quantum Core — Integration Tests: ConfigState Snapshot and Runtime Consistency
───────────────────────────────────────────────────────────────────────────────
Validate the deterministic, thread-safe, and immutable behavior of the
ConfigState singleton used by the Quantum Core runtime.
"""

from __future__ import annotations

import copy
import os
import threading
import time

from pathlib import Path

import pytest

from quantum.infrastructure.config.runtime.state import ConfigState


# ╭────────────────────────────────────────────────────────────────────────────╮
# │ Initial state and immutability                                             │
# ╰────────────────────────────────────────────────────────────────────────────╯
@pytest.mark.validation
def test_initial_state_is_clean_and_immutable(iso_env):
    """
    On first instantiation, ConfigState must be empty and its snapshot immutable
    """
    state = ConfigState.instance()
    snap = state.snapshot()

    assert state is ConfigState.instance()
    assert snap["base_dir"] is None
    assert snap["loaded_pid"] is None
    assert snap["env_cache"] == {}

    snap["env_cache"]["FAKE"] = "x"
    assert "FAKE" not in state.get_env_cache()
    assert snap is not state.snapshot()


# ╭────────────────────────────────────────────────────────────────────────────╮
# │ Update and snapshot coherence                                              │
# ╰────────────────────────────────────────────────────────────────────────────╯
@pytest.mark.validation
def test_update_and_snapshot_consistency(tmp_path: Path, iso_env):
    """
    Updating base_dir, pid, and env_cache must be reflected in snapshot()
    """
    state = ConfigState.instance()
    state.reset()

    env = {"FOO": "bar", "QUANTUM_ENV": "test"}
    state.update(base_dir=tmp_path, loaded_pid=os.getpid(), env_cache=env)
    snap = state.snapshot()

    assert snap["base_dir"] == str(tmp_path)
    assert snap["loaded_pid"] == os.getpid()
    assert snap["env_cache"]["FOO"] == "bar"
    assert state.has_valid_cache()


# ╭────────────────────────────────────────────────────────────────────────────╮
# │ Reset and deterministic reinitialization                                   │
# ╰────────────────────────────────────────────────────────────────────────────╯
@pytest.mark.validation
def test_reset_clears_state_deterministically(tmp_path: Path, iso_env):
    """
    reset() must clear all internal state, restoring a clean snapshot
    """
    state = ConfigState.instance()
    state.update(base_dir=tmp_path, loaded_pid=os.getpid(), env_cache={"K": "V"})
    state.reset()

    snap = state.snapshot()
    assert snap["base_dir"] is None
    assert snap["loaded_pid"] is None
    assert snap["env_cache"] == {}
    assert state.has_valid_cache() is False


# ╭────────────────────────────────────────────────────────────────────────────╮
# │ Stability between consecutive snapshots                                    │
# ╰────────────────────────────────────────────────────────────────────────────╯
@pytest.mark.validation
def test_stable_snapshots_without_mutation(tmp_path: Path, iso_env):
    """
    Two consecutive snapshots without mutation must be identical by value
    """
    state = ConfigState.instance()
    state.reset()
    state.update(base_dir=tmp_path, env_cache={"FOO": "bar"}, loaded_pid=os.getpid())

    s1 = copy.deepcopy(state.snapshot())
    time.sleep(0.01)
    s2 = copy.deepcopy(state.snapshot())

    assert s1 == s2
    assert s1 is not s2


# ╭────────────────────────────────────────────────────────────────────────────╮
# │ Thread safety of concurrent access() calls                                 │
# ╰────────────────────────────────────────────────────────────────────────────╯
@pytest.mark.validation
def test_concurrent_access_thread_safety(tmp_path: Path, iso_env):
    """
    Concurrent calls to access() must preserve atomicity and consistency
    """
    state = ConfigState.instance()
    state.reset()
    state.update(base_dir=tmp_path, env_cache={"CNT": "0"}, loaded_pid=os.getpid())

    results: list[int] = []

    def increment():
        def op():
            val = int(state.get_env_cache()["CNT"])
            env = state.get_env_cache()
            env["CNT"] = str(val + 1)
            state.update(env_cache=env)
            return val + 1

        results.append(state.access(op))

    threads = [threading.Thread(target=increment) for _ in range(20)]
    for t in threads:
        t.start()
    for t in threads:
        t.join(timeout=3)

    snap = state.snapshot()
    final = int(snap["env_cache"]["CNT"])
    assert final == len(threads)
    assert sorted(results) == list(range(1, len(threads) + 1))


# ╭────────────────────────────────────────────────────────────────────────────╮
# │ has_valid_cache() correctness                                              │
# ╰────────────────────────────────────────────────────────────────────────────╯
@pytest.mark.validation
def test_has_valid_cache_behaves_correctly(tmp_path: Path, iso_env):
    """
    has_valid_cache() must return True only when cache is populated
    and PID matches the current process
    """
    state = ConfigState.instance()
    state.reset()
    assert not state.has_valid_cache()

    state.update(base_dir=tmp_path, loaded_pid=os.getpid(), env_cache={"A": "B"})
    assert state.has_valid_cache()

    state.update(env_cache={})
    assert not state.has_valid_cache()

    state.update(loaded_pid=999999)
    assert not state.has_valid_cache()


# ╭────────────────────────────────────────────────────────────────────────────╮
# │ describe() diagnostic output                                               │
# ╰────────────────────────────────────────────────────────────────────────────╯
@pytest.mark.validation
def test_describe_reflects_internal_state(tmp_path: Path, iso_env):
    """
    describe() must produce a stable and human-readable representation
    """
    state = ConfigState.instance()
    state.reset()
    state.update(base_dir=tmp_path, env_cache={"X": "Y"}, loaded_pid=os.getpid())

    desc1 = state.describe()
    desc2 = state.describe()

    assert isinstance(desc1, str)
    assert "ConfigState" in desc1
    assert str(tmp_path) in desc1
    assert "env_vars=1" in desc1
    assert desc1 == desc2
