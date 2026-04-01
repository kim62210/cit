from __future__ import annotations

import json

from cit.cli import main
from cit.commands.doctor import (
    _check_config,
    _check_keychain,
    _check_lock,
    _check_paths,
    _check_profiles,
    _check_state,
    _check_wal,
    has_errors,
    has_warnings,
)
from cit.core.state import set_active_profile, push_stash_id
from cit.core import wal


def test_doctor_runs_successfully(runner, env_paths, monkeypatch):
    monkeypatch.setattr(
        "cit.core.keychain.read_keychain_payload",
        lambda: {"claudeAiOauth": {"subscriptionType": "max"}},
    )
    monkeypatch.setattr(
        "cit.core.keychain.validate_keychain_access",
        lambda: None,
    )

    result = runner.invoke(main, ["doctor"])

    assert result.exit_code == 0
    assert "Running cit diagnostics" in result.output


def test_doctor_json_output(runner, env_paths, monkeypatch):
    monkeypatch.setattr(
        "cit.core.keychain.read_keychain_payload",
        lambda: {"claudeAiOauth": {"subscriptionType": "max"}},
    )
    monkeypatch.setattr(
        "cit.core.keychain.validate_keychain_access",
        lambda: None,
    )

    result = runner.invoke(main, ["doctor", "--json"])

    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert "ok" in payload
    assert "errors" in payload
    assert "warnings" in payload
    assert "checks" in payload


def test_check_wal_no_file(runner, env_paths):
    result = _check_wal()
    assert result.status == "ok"
    assert "No WAL file" in result.detail


def test_check_wal_corrupted(runner, env_paths):
    wal_path = wal.wal_path()
    wal_path.parent.mkdir(parents=True, exist_ok=True)
    wal_path.write_text("not valid json {{{")
    result = _check_wal()
    assert result.status == "error"
    assert "corrupted" in result.detail.lower()


def test_check_wal_pending(runner, env_paths):
    wal_path = wal.wal_path()
    wal_path.parent.mkdir(parents=True, exist_ok=True)
    wal.write_wal({"step": 1, "backup": {"keychain": {}}})
    result = _check_wal()
    assert result.status == "warning"
    wal.clear_wal()


def test_check_keychain_ok(runner, env_paths, monkeypatch):
    monkeypatch.setattr(
        "cit.core.keychain.read_keychain_payload",
        lambda: {"claudeAiOauth": {"subscriptionType": "max"}},
    )
    monkeypatch.setattr(
        "cit.core.keychain.validate_keychain_access",
        lambda: None,
    )
    result = _check_keychain()
    assert result.status == "ok"
    assert "Access OK" in result.detail


def test_check_keychain_error(runner, env_paths, monkeypatch):
    def raise_error():
        raise RuntimeError("Keychain access denied")

    monkeypatch.setattr("cit.core.keychain.validate_keychain_access", raise_error)
    result = _check_keychain()
    assert result.status == "error"
    assert "Keychain access denied" in result.detail


def test_check_config_no_file(runner, env_paths):
    result = _check_config()
    assert result.status == "ok"
    assert "No config.toml" in result.detail


def test_check_config_valid(runner, env_paths):
    from cit.core import config_manager

    config_manager.config_path()
    config_path = env_paths["cit_home"] / "config.toml"
    config_path.write_text('[profile.work]\nmodel = "opus"\n')
    result = _check_config()
    assert result.status == "ok"
    assert "Valid TOML" in result.detail


def test_check_config_invalid(runner, env_paths):
    from cit.core import config_manager

    config_manager.config_path()
    config_path = env_paths["cit_home"] / "config.toml"
    config_path.write_text("not valid toml = ")
    result = _check_config()
    assert result.status == "error"
    assert "Invalid TOML" in result.detail


def test_check_profiles_no_profiles(runner, env_paths):
    result = _check_profiles()
    assert result.status == "ok"
    assert "No saved profiles" in result.detail


def test_check_profiles_with_profiles(runner, env_paths, monkeypatch):
    monkeypatch.setattr(
        "cit.core.keychain.read_keychain_payload",
        lambda: {"claudeAiOauth": {}},
    )
    from cit.core.profile import save_current_profile

    save_current_profile("work")
    result = _check_profiles()
    assert result.status == "ok"
    assert "work" in result.detail


def test_check_state_no_file(runner, env_paths):
    result = _check_state()
    assert result.status == "ok"
    assert "No state.json" in result.detail


def test_check_state_valid(runner, env_paths):
    set_active_profile("work", "personal")
    push_stash_id("12345")
    result = _check_state()
    assert result.status == "ok"
    assert "active=work" in result.detail
    assert "previous=personal" in result.detail
    assert "stash=1" in result.detail


def test_check_lock_no_lock(runner, env_paths):
    result = _check_lock()
    assert result.status == "ok"
    assert "No lock file" in result.detail


def test_check_paths_ok(runner, env_paths):
    env_paths["cit_home"].mkdir(parents=True, exist_ok=True)
    result = _check_paths()
    assert result.status == "ok"
    assert "CIT_HOME" in result.detail


def test_has_errors_true():
    from cit.commands.doctor import DiagnosticResult

    results = [
        DiagnosticResult(name="WAL", status="error", detail=" corrupted"),
        DiagnosticResult(name="Keychain", status="ok"),
    ]
    assert has_errors(results) is True


def test_has_errors_false():
    from cit.commands.doctor import DiagnosticResult

    results = [
        DiagnosticResult(name="WAL", status="ok"),
        DiagnosticResult(name="Keychain", status="warning"),
    ]
    assert has_errors(results) is False


def test_has_warnings_true():
    from cit.commands.doctor import DiagnosticResult

    results = [
        DiagnosticResult(name="WAL", status="warning"),
        DiagnosticResult(name="Keychain", status="ok"),
    ]
    assert has_warnings(results) is True


def test_has_warnings_false():
    from cit.commands.doctor import DiagnosticResult

    results = [
        DiagnosticResult(name="WAL", status="ok"),
        DiagnosticResult(name="Keychain", status="ok"),
    ]
    assert has_warnings(results) is False
