import threading

import pytest

from quantum.infrastructure.config.runtime.state import ConfigState


@pytest.mark.unit
def test_instance_returns_singleton():
    """Two calls to instance() must return the exact same object."""
    s1 = ConfigState.instance()
    s2 = ConfigState.instance()
    assert s1 is s2
    assert id(s1) == id(s2)


@pytest.mark.unit
def test_snapshot_reflects_updates(tmp_path):
    """snapshot() must reflect updates after atomic mutation."""
    state = ConfigState.instance()
    state.reset()
    base_dir = tmp_path
    env_cache = {"QUANTUM_ENV": "test"}
    state.update(base_dir=base_dir, loaded_pid=1234, env_cache=env_cache)

    snap = state.snapshot()
    assert snap["base_dir"] == str(base_dir)
    assert snap["loaded_pid"] == 1234
    assert snap["env_cache"]["QUANTUM_ENV"] == "test"


@pytest.mark.unit
def test_get_env_cache_returns_copy():
    """get_env_cache() must return a copy, not a direct reference."""
    state = ConfigState.instance()
    state.reset()
    state.update(env_cache={"A": "1"})
    cache_copy = state.get_env_cache()
    cache_copy["A"] = "999"
    assert state.get_env_cache()["A"] == "1"


@pytest.mark.unit
def test_reset_clears_state():
    """reset() must remove all internal data."""
    state = ConfigState.instance()
    state.update(base_dir="/tmp", loaded_pid=123, env_cache={"X": "1"})
    state.reset()
    snap = state.snapshot()
    assert snap["base_dir"] is None
    assert snap["loaded_pid"] is None
    assert snap["env_cache"] == {}


@pytest.mark.unit
def test_thread_safety_of_instance():
    """Multiple threads must all reference the same singleton."""
    results = []

    def _worker():
        results.append(ConfigState.instance())

    threads = [threading.Thread(target=_worker) for _ in range(10)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert len({id(r) for r in results}) == 1


@pytest.mark.unit
def test_describe_contains_expected_fields():
    """describe() output must include PID, base_dir, and env_vars count."""
    state = ConfigState.instance()
    state.reset()
    state.update(base_dir="/opt/app", loaded_pid=42, env_cache={"FOO": "BAR"})
    desc = state.describe()
    assert "ConfigState" in desc
    assert "pid=" in desc
    assert "env_vars=" in desc


@pytest.mark.unit
def test_has_valid_cache_behaviour(monkeypatch):
    """has_valid_cache() must depend on PID and env presence."""
    state = ConfigState.instance()
    state.reset()
    state.update(loaded_pid=9999, env_cache={"X": "1"})

    # Mismatch PID
    monkeypatch.setattr("os.getpid", lambda: 42)
    assert not state.has_valid_cache()

    # Matching PID
    monkeypatch.setattr("os.getpid", lambda: 9999)
    assert state.has_valid_cache()
