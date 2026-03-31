from __future__ import annotations

import stat

from cit.cli import main


def test_branch_saves_and_lists_profiles(runner, env_paths, monkeypatch):
    monkeypatch.setattr(
        "cit.core.keychain.read_keychain_payload",
        lambda: {
            "claudeAiOauth": {"subscriptionType": "team", "rateLimitTier": "tier"}
        },
    )

    save_result = runner.invoke(main, ["branch", "work", "--with-config"])
    list_result = runner.invoke(main, ["branch", "-v"])

    assert save_result.exit_code == 0
    assert "Saved current account as work" in save_result.output
    assert list_result.exit_code == 0
    assert "active@example.com" in list_result.output
    assert "team (tier)" in list_result.output

    profile_dir = env_paths["cit_home"] / "profiles" / "work"
    keychain_file = profile_dir / "keychain.json"
    assert stat.S_IMODE(profile_dir.stat().st_mode) == 0o700
    assert stat.S_IMODE(keychain_file.stat().st_mode) == 0o600
