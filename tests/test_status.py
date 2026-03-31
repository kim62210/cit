from __future__ import annotations

from cit.cli import main
from cit.core.state import set_active_profile, push_stash_id


def test_status_short_shows_profile_account_and_model(runner, env_paths, monkeypatch):
    monkeypatch.setattr(
        "cit.core.keychain.read_keychain_payload",
        lambda: {
            "claudeAiOauth": {
                "subscriptionType": "max",
                "rateLimitTier": "default_claude_max_20x",
                "expiresAt": 4102444800000,
            }
        },
    )
    set_active_profile("work", "personal")
    push_stash_id("12345")

    result = runner.invoke(main, ["status", "--short"])

    assert result.exit_code == 0
    assert "work active@example.com max opus" in result.output
