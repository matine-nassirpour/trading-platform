import pytest

from quantum.infrastructure.config.models.mt5 import MT5Settings


@pytest.mark.verification
def test_mt5_settings_defaults_are_safe():
    """Defaults must define consistent timeouts and credentials placeholders."""
    s = MT5Settings()  # type: ignore[arg-type]
    assert hasattr(s, "quantum_mt5_ftmo_login")
    assert hasattr(s, "quantum_mt5_ftmo_server")
    assert hasattr(s, "quantum_mt5_ftmo_password")
    assert hasattr(s, "quantum_mt5_fundednext_login")
    assert hasattr(s, "quantum_mt5_fundednext_server")
    assert hasattr(s, "quantum_mt5_fundednext_password")
    assert hasattr(s, "mt5_ftmo_terminal_path")
    assert hasattr(s, "mt5_fundednext_terminal_path")


@pytest.mark.verification
def test_mt5_settings_roundtrip():
    """model_dump()/model_validate() roundtrip must preserve semantics."""
    s = MT5Settings(
        quantum_mt5_ftmo_login=123456,
        quantum_mt5_ftmo_server="Demo-Server",
        quantum_mt5_ftmo_password="secret",  # pragma: allowlist secret
    )  # type: ignore[arg-type]
    clone = MT5Settings.model_validate(s.model_dump())
    assert clone.quantum_mt5_ftmo_server == "Demo-Server"
    assert clone.quantum_mt5_ftmo_login == 123456
