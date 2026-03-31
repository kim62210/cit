from __future__ import annotations

import json

from cit.cli import main
from cit.core.config_manager import set_config_value
from cit.core.profile import save_current_profile
from cit.core.state import read_state, set_active_profile


def test_checkout_switches_profile_and_updates_state(runner, env_paths, monkeypatch):
    active_keychain = {
        "claudeAiOauth": {"subscriptionType": "max", "rateLimitTier": "default"}
    }
    target_keychain = {
        "claudeAiOauth": {"subscriptionType": "team", "rateLimitTier": "work"}
    }
    keychain_store = {"payload": active_keychain}

    monkeypatch.setattr(
        "cit.core.keychain.read_keychain_payload", lambda: keychain_store["payload"]
    )
    monkeypatch.setattr("cit.core.keychain.validate_keychain_access", lambda: None)
    monkeypatch.setattr(
        "cit.core.keychain.write_keychain_payload",
        lambda payload: keychain_store.__setitem__("payload", payload),
    )
    set_active_profile("personal", None)
    save_current_profile("work", with_config=True)
    work_oauth = json.loads(env_paths["claude_json"].read_text())
    work_oauth["oauthAccount"]["emailAddress"] = "work@example.com"
    env_paths["claude_json"].write_text(json.dumps(work_oauth))
    keychain_store["payload"] = target_keychain
    save_current_profile("office", with_config=True)
    keychain_store["payload"] = active_keychain

    result = runner.invoke(main, ["checkout", "office"])

    assert result.exit_code == 0
    assert "Switched to context 'office'" in result.output
    state = read_state()
    assert state["activeProfile"] == "office"
    assert state["previousProfile"] == "personal"


def test_checkout_applies_profile_config_to_claude_files(
    runner, env_paths, monkeypatch
):
    keychain_store = {
        "payload": {
            "claudeAiOauth": {"subscriptionType": "max", "rateLimitTier": "default"}
        }
    }

    monkeypatch.setattr(
        "cit.core.keychain.read_keychain_payload", lambda: keychain_store["payload"]
    )
    monkeypatch.setattr("cit.core.keychain.validate_keychain_access", lambda: None)
    monkeypatch.setattr(
        "cit.core.keychain.write_keychain_payload",
        lambda payload: keychain_store.__setitem__("payload", payload),
    )

    set_active_profile("personal", None)
    save_current_profile("personal", with_config=True)

    target_oauth = json.loads(env_paths["claude_json"].read_text())
    target_oauth["oauthAccount"]["emailAddress"] = "office@example.com"
    env_paths["claude_json"].write_text(json.dumps(target_oauth))
    (env_paths["claude_home"] / "settings.json").write_text(
        json.dumps({"model": "sonnet"})
    )
    (env_paths["claude_home"] / ".mcp.json").write_text(
        json.dumps({"legacy": {"command": "old"}})
    )
    save_current_profile("office", with_config=True)

    set_config_value("model", "opus[1m]", "office")
    set_config_value("permission-mode", "dangerousSkipPermissions", "office")
    set_config_value(
        "mcp.memory",
        '{"command": "npx", "args": ["@anthropic/memory-mcp"]}',
        "office",
    )

    (env_paths["claude_home"] / "settings.json").write_text(
        json.dumps({"model": "haiku"})
    )
    (env_paths["claude_home"] / ".mcp.json").write_text(json.dumps({}))

    result = runner.invoke(main, ["checkout", "office"])

    assert result.exit_code == 0
    settings = json.loads((env_paths["claude_home"] / "settings.json").read_text())
    mcp = json.loads((env_paths["claude_home"] / ".mcp.json").read_text())
    assert settings["model"] == "opus[1m]"
    assert settings["permission-mode"] == "dangerousSkipPermissions"
    assert mcp["memory"]["command"] == "npx"


def test_checkout_skips_auto_stash_when_current_profile_is_unchanged(
    runner, env_paths, monkeypatch
):
    keychain_store = {
        "payload": {
            "claudeAiOauth": {"subscriptionType": "max", "rateLimitTier": "default"}
        }
    }

    monkeypatch.setattr(
        "cit.core.keychain.read_keychain_payload", lambda: keychain_store["payload"]
    )
    monkeypatch.setattr("cit.core.keychain.validate_keychain_access", lambda: None)
    monkeypatch.setattr(
        "cit.core.keychain.write_keychain_payload",
        lambda payload: keychain_store.__setitem__("payload", payload),
    )

    set_active_profile("personal", None)
    save_current_profile("personal", with_config=True)

    office_oauth = json.loads(env_paths["claude_json"].read_text())
    office_oauth["oauthAccount"]["emailAddress"] = "office@example.com"
    env_paths["claude_json"].write_text(json.dumps(office_oauth))
    keychain_store["payload"] = {"claudeAiOauth": {"subscriptionType": "team"}}
    save_current_profile("office", with_config=True)

    keychain_store["payload"] = {
        "claudeAiOauth": {"subscriptionType": "max", "rateLimitTier": "default"}
    }
    original_oauth = office_oauth
    original_oauth["oauthAccount"]["emailAddress"] = "active@example.com"
    env_paths["claude_json"].write_text(json.dumps(original_oauth))

    result = runner.invoke(main, ["checkout", "office"])

    assert result.exit_code == 0
    assert read_state()["stashStack"] == []


def test_checkout_warns_when_claude_process_is_running(runner, env_paths, monkeypatch):
    keychain_store = {"payload": {"claudeAiOauth": {"subscriptionType": "max"}}}

    monkeypatch.setattr(
        "cit.core.keychain.read_keychain_payload", lambda: keychain_store["payload"]
    )
    monkeypatch.setattr("cit.core.keychain.validate_keychain_access", lambda: None)
    monkeypatch.setattr(
        "cit.core.keychain.write_keychain_payload",
        lambda payload: keychain_store.__setitem__("payload", payload),
    )
    monkeypatch.setattr(
        "cit.commands.checkout.has_running_claude_process", lambda: True
    )

    set_active_profile("personal", None)
    save_current_profile("office", with_config=True)

    result = runner.invoke(main, ["checkout", "office"])

    assert result.exit_code == 0
    assert "Warning: Claude appears to be running" in result.output


def test_checkout_dry_run_shows_plan_without_mutating_state(
    runner, env_paths, monkeypatch
):
    keychain_store = {
        "payload": {
            "claudeAiOauth": {"subscriptionType": "max", "rateLimitTier": "default"}
        }
    }
    write_calls: list[dict[str, object]] = []

    monkeypatch.setattr(
        "cit.core.keychain.read_keychain_payload", lambda: keychain_store["payload"]
    )
    monkeypatch.setattr(
        "cit.core.keychain.write_keychain_payload",
        lambda payload: write_calls.append(payload),
    )
    monkeypatch.setattr("cit.core.keychain.validate_keychain_access", lambda: None)
    monkeypatch.setattr(
        "cit.commands.checkout.has_running_claude_process", lambda: True
    )

    set_active_profile("personal", None)
    save_current_profile("personal", with_config=True)

    target_oauth = json.loads(env_paths["claude_json"].read_text())
    target_oauth["oauthAccount"]["emailAddress"] = "office@example.com"
    env_paths["claude_json"].write_text(json.dumps(target_oauth))
    (env_paths["claude_home"] / "settings.json").write_text(
        json.dumps({"model": "sonnet"})
    )
    (env_paths["claude_home"] / ".mcp.json").write_text(
        json.dumps({"legacy": {"command": "old"}})
    )
    keychain_store["payload"] = {
        "claudeAiOauth": {"subscriptionType": "team", "rateLimitTier": "work"}
    }
    save_current_profile("office", with_config=True)

    keychain_store["payload"] = {
        "claudeAiOauth": {"subscriptionType": "max", "rateLimitTier": "default"}
    }
    source_oauth = json.loads(env_paths["claude_json"].read_text())
    source_oauth["oauthAccount"]["emailAddress"] = "active@example.com"
    env_paths["claude_json"].write_text(json.dumps(source_oauth))
    (env_paths["claude_home"] / "settings.json").write_text(
        json.dumps({"model": "haiku"})
    )
    (env_paths["claude_home"] / ".mcp.json").write_text(json.dumps({}))

    set_config_value("model", "opus[1m]", "office")
    set_config_value("permission-mode", "dangerousSkipPermissions", "office")
    set_config_value(
        "mcp.memory",
        '{"command": "npx", "args": ["@anthropic/memory-mcp"]}',
        "office",
    )

    result = runner.invoke(main, ["checkout", "office", "--dry-run"])

    assert result.exit_code == 0
    assert "Dry run: checkout 'office'" in result.output
    assert "Profile: personal -> office" in result.output
    assert "Account: active@example.com -> office@example.com" in result.output
    assert "~ model: haiku -> opus[1m]" in result.output
    assert "+ mcp.memory" in result.output
    assert "! auto-stash: yes" in result.output
    assert "! warning: Claude appears to be running" in result.output
    assert read_state()["activeProfile"] == "personal"
    assert write_calls == []


def test_checkout_dry_run_reports_missing_profile_cleanly(runner, env_paths):
    result = runner.invoke(main, ["checkout", "missing", "--dry-run"])

    assert result.exit_code == 1
    assert "Error: Profile not found: missing" in result.output
