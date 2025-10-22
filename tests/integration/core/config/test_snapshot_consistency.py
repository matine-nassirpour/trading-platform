from __future__ import annotations

import copy
import os
import threading
import time
from pathlib import Path

import pytest

from quantum.core.config.runtime.state import ConfigState


# ╭─────────────────────────────────────────────────────────────────────────────╮
# │ 1. Initial state and immutability                                           │
# ╰─────────────────────────────────────────────────────────────────────────────╯
@pytest.mark.integration
def test_initial_state_is_clean_and_immutable(iso_env):
    """
    On first instantiation, ConfigState must be empty and immutable.
    """
    state = ConfigState.instance()
    snap = state.snapshot()

    assert snap["base_dir"] is None
    assert snap["loaded_pid"] is None
    assert snap["env_cache"] == {}

    # Snapshot returns copies, not references
    snap["env_cache"]["FAKE"] = "x"
    assert "FAKE" not in state.get_env_cache()


# ╭─────────────────────────────────────────────────────────────────────────────╮
# │ 2. Update and snapshot coherence                                            │
# ╰─────────────────────────────────────────────────────────────────────────────╯
@pytest.mark.integration
def test_update_and_snapshot_consistency(tmp_path: Path, iso_env):
    """
    Updating base_dir, pid and env_cache must be reflected in snapshot().
    """
    state = ConfigState.instance()
    state.reset()

    base_dir = tmp_path
    env = {"FOO": "bar", "QUANTUM_ENV": "test"}

    state.update(base_dir=base_dir, loaded_pid=os.getpid(), env_cache=env)
    snap = state.snapshot()

    assert snap["base_dir"] == str(base_dir)
    assert snap["loaded_pid"] == os.getpid()
    assert snap["env_cache"]["FOO"] == "bar"


# ╭─────────────────────────────────────────────────────────────────────────────╮
# │ 3. Reset and deterministic reinitialization                                 │
# ╰─────────────────────────────────────────────────────────────────────────────╯
@pytest.mark.integration
def test_reset_clears_state_deterministically(tmp_path: Path, iso_env):
    """
    reset() must clear all internal state, restoring a clean snapshot.
    """
    state = ConfigState.instance()
    state.update(
        base_dir=tmp_path,
        loaded_pid=os.getpid(),
        env_cache={"K": "V"},
    )
    state.reset()
    snap = state.snapshot()

    assert snap["base_dir"] is None
    assert snap["loaded_pid"] is None
    assert snap["env_cache"] == {}


# ╭─────────────────────────────────────────────────────────────────────────────╮
# │ 4. Stability between consecutive snapshots                                  │
# ╰─────────────────────────────────────────────────────────────────────────────╯
@pytest.mark.integration
def test_stable_snapshots_without_mutation(tmp_path: Path, iso_env):
    """
    Two consecutive snapshots without mutation must be identical by value.
    """
    state = ConfigState.instance()
    state.reset()
    state.update(base_dir=tmp_path, env_cache={"FOO": "bar"}, loaded_pid=os.getpid())

    s1 = copy.deepcopy(state.snapshot())
    time.sleep(0.01)
    s2 = copy.deepcopy(state.snapshot())

    assert s1 == s2, "Snapshots differ without state mutation"


# ╭─────────────────────────────────────────────────────────────────────────────╮
# │ 5. Thread safety of concurrent access() calls                               │
# ╰─────────────────────────────────────────────────────────────────────────────╯
@pytest.mark.integration
def test_concurrent_access_thread_safety(tmp_path: Path, iso_env):
    """
    concurrent calls to access() must preserve atomicity and consistency.
    """
    state = ConfigState.instance()
    state.reset()
    state.update(base_dir=tmp_path, env_cache={"CNT": "0"}, loaded_pid=os.getpid())

    results: list[int] = []

    def increment():
        def op():
            val = int(state._env_cache["CNT"])
            val += 1
            state._env_cache["CNT"] = str(val)
            return val

        results.append(state.access(op))

    threads = [threading.Thread(target=increment) for _ in range(20)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    # All increments executed atomically, final count = number of threads
    final = int(state.snapshot()["env_cache"]["CNT"])
    assert final == 20
    assert len(results) == 20
    assert sorted(results) == list(range(1, 21))


# ╭─────────────────────────────────────────────────────────────────────────────╮
# │ 6. has_valid_cache() correctness                                            │
# ╰─────────────────────────────────────────────────────────────────────────────╯
@pytest.mark.integration
def test_has_valid_cache_behaves_correctly(tmp_path: Path, iso_env):
    """
    has_valid_cache() must return True only when env_cache is populated
    and the loaded_pid matches the current process.
    """
    state = ConfigState.instance()
    state.reset()
    assert state.has_valid_cache() is False

    state.update(base_dir=tmp_path, loaded_pid=os.getpid(), env_cache={"A": "B"})
    assert state.has_valid_cache() is True

    # Simulate process mismatch
    state.update(loaded_pid=999999)
    assert state.has_valid_cache() is False


# ╭─────────────────────────────────────────────────────────────────────────────╮
# │ 7. describe() diagnostic output                                             │
# ╰─────────────────────────────────────────────────────────────────────────────╯
@pytest.mark.integration
def test_describe_reflects_internal_state(tmp_path: Path, iso_env):
    """
    describe() must produce a stable and human-readable representation.
    """
    state = ConfigState.instance()
    state.reset()
    state.update(base_dir=tmp_path, env_cache={"X": "Y"}, loaded_pid=os.getpid())

    desc = state.describe()
    assert isinstance(desc, str)
    assert "ConfigState" in desc
    assert str(tmp_path) in desc
    assert "env_vars=1" in desc
