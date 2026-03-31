from __future__ import annotations

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
