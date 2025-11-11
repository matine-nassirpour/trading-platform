import os

from pathlib import Path

import pytest

from quantum.infrastructure.config.providers import env_loader
from quantum.infrastructure.config.runtime.state import ConfigState


@pytest.mark.verification
def test_merge_envs_applies_last_wins_policy():
    """Later layers override earlier ones and None values are ignored."""
    merged = env_loader._merge_envs(
        {"A": "1", "B": "x"},
        {"B": "2", "C": None},
        {"C": "3"},
    )
    assert merged == {"A": "1", "B": "2", "C": "3"}


@pytest.mark.verification
def test_resolve_env_path_prefers_explicit_file(tmp_path: Path):
    """Explicit env_file path must take precedence over root directory."""
    env_file = tmp_path / ".env"
    env_file.write_text("QUANTUM_ENV=dev", encoding="utf-8")

    base_dir, resolved = env_loader._resolve_env_path(root=tmp_path, env_file=env_file)
    assert resolved == env_file
    assert base_dir == tmp_path


@pytest.mark.verification
def test_resolve_env_path_falls_back_to_cwd(monkeypatch, tmp_path: Path):
    """When no .env file exists, must fall back to current working directory."""
    monkeypatch.chdir(tmp_path)
    base_dir, resolved = env_loader._resolve_env_path(root=None, env_file=None)
    assert base_dir == tmp_path
    assert resolved is None


@pytest.mark.verification
def test_load_env_without_apply_does_not_modify_os_environ(monkeypatch, tmp_path: Path):
    """apply=False must not alter os.environ nor persist environment state."""
    monkeypatch.setattr(
        env_loader, "dotenv_values", lambda *a, **kw: {"QUANTUM_ENV": "test"}
    )
    monkeypatch.setattr(env_loader, "find_dotenv", lambda *a, **kw: None)
    monkeypatch.chdir(tmp_path)

    before = dict(os.environ)
    result = env_loader.load_env(apply=False)
    after = dict(os.environ)

    assert before == after
    assert result["QUANTUM_ENV"] == "test"


@pytest.mark.verification
def test_load_env_with_apply_injects_variables(monkeypatch, tmp_path: Path):
    """apply=True must inject merged variables into os.environ."""
    monkeypatch.setattr(
        env_loader, "dotenv_values", lambda *a, **kw: {"QUANTUM_ENV": "prod"}
    )
    monkeypatch.setattr(env_loader, "find_dotenv", lambda *a, **kw: None)
    monkeypatch.chdir(tmp_path)

    env_loader.load_env(apply=True)
    assert os.environ.get("QUANTUM_ENV") == "prod"


@pytest.mark.verification
def test_load_env_returns_merged_environment(monkeypatch, tmp_path: Path):
    """load_env() must return a merged environment and update ConfigState."""
    monkeypatch.setattr(
        env_loader, "dotenv_values", lambda *a, **kw: {"QUANTUM_ENV": "staging"}
    )
    monkeypatch.setattr(env_loader, "find_dotenv", lambda *a, **kw: None)
    monkeypatch.chdir(tmp_path)

    state = ConfigState.instance()
    state.reset()

    result = env_loader.load_env()
    snap = state.snapshot()

    assert "QUANTUM_ENV" in result
    assert result["QUANTUM_ENV"] == "staging"
    assert "QUANTUM_ENV" in snap["env_cache"]
    assert snap["env_cache"]["QUANTUM_ENV"] == "staging"


@pytest.mark.verification
def test_load_env_uses_cache_if_valid(monkeypatch, tmp_path: Path):
    """Second call must reuse the cached environment if still valid."""
    monkeypatch.setattr(
        env_loader, "dotenv_values", lambda *a, **kw: {"QUANTUM_ENV": "test"}
    )
    monkeypatch.setattr(env_loader, "find_dotenv", lambda *a, **kw: None)
    monkeypatch.chdir(tmp_path)

    state = ConfigState.instance()
    state.reset()

    first = env_loader.load_env(apply=False)
    second = env_loader.load_env(apply=False)

    # Cache reuse → no recomputation → identical dicts
    assert first == second
    assert state.has_valid_cache()
    snap = state.snapshot()
    assert snap["env_cache"]["QUANTUM_ENV"] == "test"


@pytest.mark.verification
def test_load_env_with_override_replaces_existing(monkeypatch, tmp_path: Path):
    """override=True must replace existing environment variables."""
    os.environ["FOO"] = "old"
    monkeypatch.setattr(env_loader, "dotenv_values", lambda *a, **kw: {"FOO": "new"})
    monkeypatch.setattr(env_loader, "find_dotenv", lambda *a, **kw: None)
    monkeypatch.chdir(tmp_path)

    env_loader.load_env(apply=True, override=True)
    assert os.environ["FOO"] == "new"


@pytest.mark.verification
def test_load_env_without_dotenv_module(monkeypatch):
    """When python-dotenv is not installed, load_env must still return os.environ safely."""
    monkeypatch.setattr(env_loader, "dotenv_values", None)
    monkeypatch.setattr(env_loader, "find_dotenv", None)

    result = env_loader.load_env(apply=False)
    assert isinstance(result, dict)
    assert all(isinstance(k, str) for k in result.keys())
