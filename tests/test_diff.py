from __future__ import annotations

import json

from cit.cli import main
from cit.core.config_manager import set_config_value
from cit.core.profile import save_current_profile


def test_diff_shows_changes_between_two_profiles(runner, env_paths, monkeypatch):
    keychain_store = {
        "payload": {
            "claudeAiOauth": {"subscriptionType": "max", "rateLimitTier": "default"}
        }
    }

    monkeypatch.setattr(
        "cit.core.keychain.read_keychain_payload", lambda: keychain_store["payload"]
    )

    save_current_profile("personal", with_config=True)

    work_oauth = json.loads(env_paths["claude_json"].read_text())
    work_oauth["oauthAccount"]["emailAddress"] = "work@example.com"
    env_paths["claude_json"].write_text(json.dumps(work_oauth))
    (env_paths["claude_home"] / "settings.json").write_text(
        json.dumps({"model": "sonnet"})
    )
    (env_paths["claude_home"] / ".mcp.json").write_text(
        json.dumps({"legacy": {"command": "old"}})
    )
    keychain_store["payload"] = {
        "claudeAiOauth": {"subscriptionType": "team", "rateLimitTier": "work"}
    }
    save_current_profile("work", with_config=True)
    set_config_value("model", "opus[1m]", "work")
    set_config_value("permission-mode", "dangerousSkipPermissions", "work")
    set_config_value(
        "mcp.memory",
        '{"command": "npx", "args": ["@anthropic/memory-mcp"]}',
        "work",
    )

    result = runner.invoke(main, ["diff", "personal", "work"])

    assert result.exit_code == 0
    assert "Diff: personal -> work" in result.output
    assert "Account: active@example.com -> work@example.com" in result.output
    assert "~ subscription: max -> team" in result.output
    assert "~ model: opus -> opus[1m]" in result.output
    assert "~ permission-mode: unset -> dangerousSkipPermissions" in result.output
    assert "+ mcp.legacy" in result.output
    assert "+ mcp.memory" in result.output


def test_diff_reports_no_differences_for_identical_profiles(
    runner, env_paths, monkeypatch
):
    monkeypatch.setattr(
        "cit.core.keychain.read_keychain_payload",
        lambda: {
            "claudeAiOauth": {"subscriptionType": "max", "rateLimitTier": "default"}
        },
    )
    save_current_profile("personal", with_config=True)
    save_current_profile("personal-copy", with_config=True)

    result = runner.invoke(main, ["diff", "personal", "personal-copy"])

    assert result.exit_code == 0
    assert "Diff: personal -> personal-copy" in result.output
    assert "No differences found." in result.output


def test_diff_reports_missing_profile_cleanly(runner):
    result = runner.invoke(main, ["diff", "missing", "work"])

    assert result.exit_code == 1
    assert "Error: Profile not found: missing" in result.output


def test_diff_json_returns_machine_readable_payload(runner, env_paths, monkeypatch):
    keychain_store = {
        "payload": {
            "claudeAiOauth": {"subscriptionType": "max", "rateLimitTier": "default"}
        }
    }

    monkeypatch.setattr(
        "cit.core.keychain.read_keychain_payload", lambda: keychain_store["payload"]
    )

    save_current_profile("personal", with_config=True)

    work_oauth = json.loads(env_paths["claude_json"].read_text())
    work_oauth["oauthAccount"]["emailAddress"] = "work@example.com"
    env_paths["claude_json"].write_text(json.dumps(work_oauth))
    (env_paths["claude_home"] / "settings.json").write_text(
        json.dumps({"model": "sonnet"})
    )
    keychain_store["payload"] = {
        "claudeAiOauth": {"subscriptionType": "team", "rateLimitTier": "work"}
    }
    save_current_profile("work", with_config=True)
    set_config_value("model", "opus[1m]", "work")
    set_config_value("permission-mode", "dangerousSkipPermissions", "work")

    result = runner.invoke(main, ["diff", "personal", "work", "--json"])

    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert payload["from_profile"] == "personal"
    assert payload["to_profile"] == "work"
    assert payload["source"]["account"] == "active@example.com"
    assert payload["target"]["account"] == "work@example.com"
    assert payload["changes"]["subscription"] == {"from": "max", "to": "team"}
    assert payload["changes"]["model"] == {"from": "opus", "to": "opus[1m]"}
    assert payload["changes"]["permission_mode"] == {
        "from": "unset",
        "to": "dangerousSkipPermissions",
    }
