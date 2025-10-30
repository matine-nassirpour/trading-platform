"""
Quantum Core — Integration Tests: Environment Loader
────────────────────────────────────────────────────
Validate deterministic multi-layer loading, merging, and caching
of environment configurations across .env, .env.{env}, and .env.local.
"""

import os
from pathlib import Path

import pytest

from quantum.infrastructure.config.providers.env_loader import load_env
from quantum.infrastructure.config.runtime.state import ConfigState


# ╭────────────────────────────────────────────────────────────────────────────╮
# │ Layer merging and precedence                                               │
# ╰────────────────────────────────────────────────────────────────────────────╯
@pytest.mark.integration
def test_env_loader_merges_layers(tmp_path: Path, iso_env):
    """
    Verify that .env, .env.local, and .env.{env} are merged deterministically
    and precedence order is respected: local > env-specific > base.
    """
    base = tmp_path / ".env"
    base.write_text("FOO=base\nBAR=base\nQUANTUM_ENV=staging\n", encoding="utf-8")

    staging = tmp_path / ".env.staging"
    staging.write_text("BAR=staging\nBAZ=staging\n", encoding="utf-8")

    local = tmp_path / ".env.local"
    local.write_text("FOO=local\nQUX=local\n", encoding="utf-8")

    merged = load_env(root=tmp_path, apply=False)

    # Core precedence assertions
    assert merged["FOO"] == "local"
    assert merged["BAR"] == "staging"
    assert merged["BAZ"] == "staging"
    assert merged["QUX"] == "local"
    assert merged["QUANTUM_ENV"] == "staging"

    # Ensure state is cached correctly
    state = ConfigState.instance()
    snap = state.snapshot()
    assert snap["loaded_pid"] == os.getpid()
    assert "env_cache" in snap and len(snap["env_cache"]) > 0

    # Reload consistency after cache reset
    ConfigState.instance().reset()
    reloaded = load_env(root=tmp_path)
    assert reloaded == merged


@pytest.mark.integration
def test_env_loader_handles_missing_layers(tmp_path: Path, iso_env):
    """
    Validate behavior when optional .env.local or .env.{env} are missing.
    The loader must degrade gracefully without exceptions.
    """
    base = tmp_path / ".env"
    base.write_text("FOO=base\nQUANTUM_ENV=staging\n", encoding="utf-8")

    # Only .env present
    merged = load_env(root=tmp_path)
    assert merged["FOO"] == "base"
    assert "QUX" not in merged


# ╭────────────────────────────────────────────────────────────────────────────╮
# │ Environment application                                                    │
# ╰────────────────────────────────────────────────────────────────────────────╯
@pytest.mark.integration
def test_env_loader_apply_and_noapply_modes(tmp_path: Path, iso_env):
    """
    Ensure apply=False preserves purity, while apply=True injects variables
    into os.environ, and verify idempotent behavior on reapply.
    """
    env_file = tmp_path / ".env"
    env_file.write_text("X=1\nY=2\n", encoding="utf-8")

    # Baseline: no side effects
    merged_no_apply = load_env(root=tmp_path, apply=False)
    assert "X" not in os.environ
    assert merged_no_apply["X"] == "1"

    # Apply=True should inject
    merged = load_env(root=tmp_path, apply=True)
    assert os.environ["X"] == "1"
    assert "Y" in merged

    # Idempotence: second call must not alter os.environ
    before = dict(os.environ)
    load_env(root=tmp_path, apply=True)
    assert os.environ == before

    # Cache must remain valid
    state = ConfigState.instance()
    assert state.has_valid_cache()


# ╭────────────────────────────────────────────────────────────────────────────╮
# │ Override semantics and cache reset                                         │
# ╰────────────────────────────────────────────────────────────────────────────╯
@pytest.mark.integration
def test_env_loader_respects_override_and_cache(tmp_path: Path, iso_env):
    """
    Verify that override=False preserves os.environ values.
    When override=True, reloading updates only after cache reset.
    """
    os.environ["EXISTING"] = "keepme"
    (tmp_path / ".env").write_text("EXISTING=new\n", encoding="utf-8")

    load_env(root=tmp_path, apply=True, override=False)
    assert os.environ["EXISTING"] == "keepme"

    state = ConfigState.instance()
    assert "EXISTING" in state.get_env_cache()

    # Force a state reset to allow reloading
    ConfigState.instance().reset()
    load_env(root=tmp_path, apply=True, override=True)
    assert os.environ["EXISTING"] == "new"
    assert ConfigState.instance().get_env_cache()["EXISTING"] == "new"


# ╭────────────────────────────────────────────────────────────────────────────╮
# │ Cache reuse and process consistency                                        │
# ╰────────────────────────────────────────────────────────────────────────────╯
@pytest.mark.integration
def test_env_loader_cache_reuse_and_pid_invalidation(tmp_path: Path, iso_env):
    """
    Verify that subsequent calls reuse the cached environment when PID unchanged,
    and invalidation occurs when PID mismatch is simulated.
    """
    env_file = tmp_path / ".env"
    env_file.write_text("FOO=bar\n", encoding="utf-8")

    first = load_env(root=tmp_path)
    state = ConfigState.instance()

    # Simulated second call (should reuse cache)
    second = load_env(root=tmp_path)
    assert first == second
    assert state.has_valid_cache()

    # Simulate another PID to invalidate cache
    state._loaded_pid = 999999  # For testing only
    assert not state.has_valid_cache()

    # Apply=True re-applies values
    ConfigState.instance().reset()
    load_env(root=tmp_path, apply=True)
    assert os.getenv("FOO") == "bar"


# ╭────────────────────────────────────────────────────────────────────────────╮
# │ Reapply Idempotence                                                        │
# ╰────────────────────────────────────────────────────────────────────────────╯
@pytest.mark.integration
def test_env_loader_reapply_is_idempotent(tmp_path: Path, iso_env):
    """
    Ensure repeated calls to load_env(apply=True) are side effect free
    when the environment is already applied and cached.
    """
    env_file = tmp_path / ".env"
    env_file.write_text("FOO=bar\n", encoding="utf-8")

    load_env(root=tmp_path, apply=True)
    before = dict(os.environ)
    load_env(root=tmp_path, apply=True)
    after = dict(os.environ)
    assert before == after
