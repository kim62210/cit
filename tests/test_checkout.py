from __future__ import annotations

import json

from cit.cli import main
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
    assert "Switched to profile 'office'" in result.output
    state = read_state()
    assert state["activeProfile"] == "office"
    assert state["previousProfile"] == "personal"
