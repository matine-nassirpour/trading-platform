"""
Quantum Core — Integration Tests: Environment Loader
────────────────────────────────────────────────────
Validate deterministic multi-layer loading, merging, and caching
of environment configurations across .env, .env.{env}, and .env.local.
"""

import os
from pathlib import Path

import pytest

from quantum.core.config.providers.env_loader import load_env
from quantum.core.config.runtime.state import ConfigState


# ╭─────────────────────────────────────────────────────────────────────────────╮
# │ Layer merging and precedence                                                │
# ╰─────────────────────────────────────────────────────────────────────────────╯
@pytest.mark.integration
def test_env_loader_merges_layers(tmp_path: Path, iso_env):
    """
    Verify that .env, .env.local, and .env.{env} are merged deterministically
    """
    # Create base, env-specific, and local env files
    base = tmp_path / ".env"
    base.write_text("FOO=base\nBAR=base\nQUANTUM_ENV=staging\n", encoding="utf-8")

    staging = tmp_path / ".env.staging"
    staging.write_text("BAR=staging\nBAZ=staging\n", encoding="utf-8")

    local = tmp_path / ".env.local"
    local.write_text("FOO=local\nQUX=local\n", encoding="utf-8")

    # Execute load_env
    merged = load_env(root=tmp_path, apply=False)

    # Assertions: deterministic precedence order
    assert merged["FOO"] == "local"
    assert merged["BAR"] == "staging"
    assert merged["BAZ"] == "staging"
    assert merged["QUX"] == "local"
    assert merged["QUANTUM_ENV"] == "staging"

    # Ensure state cached properly
    state = ConfigState.instance()
    snap = state.snapshot()
    assert "env_cache" in snap
    assert snap["loaded_pid"] == os.getpid()


# ╭─────────────────────────────────────────────────────────────────────────────╮
# │ Environment application                                                     │
# ╰─────────────────────────────────────────────────────────────────────────────╯
@pytest.mark.integration
def test_env_loader_apply_sets_environ(tmp_path: Path, iso_env):
    """
    Ensure load_env(apply=True) writes values into os.environ conditionally
    """
    env_file = tmp_path / ".env"
    env_file.write_text("X=1\nY=2\n", encoding="utf-8")

    assert "X" not in os.environ
    merged = load_env(root=tmp_path, apply=True)

    assert os.environ["X"] == "1"
    assert "X" in merged
    assert merged["Y"] == "2"


# ╭─────────────────────────────────────────────────────────────────────────────╮
# │ Override semantics and cache reset                                          │
# ╰─────────────────────────────────────────────────────────────────────────────╯
@pytest.mark.integration
def test_env_loader_respects_override(tmp_path: Path, iso_env):
    """
    Verify that override=False preserves existing os.environ values.
    When override=True, reloading takes effect only if cache is cleared
    """
    os.environ["EXISTING"] = "keepme"
    (tmp_path / ".env").write_text("EXISTING=new\n", encoding="utf-8")

    load_env(root=tmp_path, apply=True, override=False)
    assert os.environ["EXISTING"] == "keepme"

    # Force a state reset to allow reloading
    ConfigState.instance().reset()

    load_env(root=tmp_path, apply=True, override=True)
    assert os.environ["EXISTING"] == "new"


# ╭─────────────────────────────────────────────────────────────────────────────╮
# │ Cache reuse and process consistency                                         │
# ╰─────────────────────────────────────────────────────────────────────────────╯
@pytest.mark.integration
def test_env_loader_cache_reuse(tmp_path: Path, iso_env):
    """
    Verify that subsequent calls reuse the cached environment when PID unchanged
    """
    env_file = tmp_path / ".env"
    env_file.write_text("FOO=bar\n", encoding="utf-8")

    first = load_env(root=tmp_path)
    state = ConfigState.instance()

    # Simulate cached access
    second = load_env(root=tmp_path)
    assert first == second
    assert state.has_valid_cache()
