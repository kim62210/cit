from __future__ import annotations

import stat

from cit.cli import main


def test_stash_push_and_list(runner, env_paths, monkeypatch):
    monkeypatch.setattr(
        "cit.core.keychain.read_keychain_payload",
        lambda: {"claudeAiOauth": {"subscriptionType": "max"}},
    )

    push_result = runner.invoke(main, ["stash"])
    list_result = runner.invoke(main, ["stash", "list"])

    assert push_result.exit_code == 0
    assert "Saved stash@{0}" in push_result.output
    assert list_result.exit_code == 0
    assert "stash@{0}: manual stash" in list_result.output

    stash_dirs = list((env_paths["cit_home"] / "stash").iterdir())
    assert len(stash_dirs) == 1
    keychain_file = stash_dirs[0] / "keychain.json"
    assert stat.S_IMODE(stash_dirs[0].stat().st_mode) == 0o700
    assert stat.S_IMODE(keychain_file.stat().st_mode) == 0o600
