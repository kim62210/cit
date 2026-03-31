from __future__ import annotations

from cit.core.wal import clear_wal, read_wal, update_wal_step, write_wal


def test_wal_step_updates(env_paths):
    write_wal({"op": "checkout", "step": 0, "backup": {}})

    update_wal_step(2)

    assert read_wal()["step"] == 2
    clear_wal()
    assert read_wal() is None


def test_read_wal_returns_none_for_invalid_json(env_paths):
    wal_file = env_paths["cit_home"] / "wal.json"
    wal_file.parent.mkdir(parents=True, exist_ok=True)
    wal_file.write_text("{not-valid-json")

    assert read_wal() is None


def test_main_ignores_corrupt_wal_and_still_runs_command(
    runner, env_paths, monkeypatch
):
    wal_file = env_paths["cit_home"] / "wal.json"
    wal_file.parent.mkdir(parents=True, exist_ok=True)
    wal_file.write_text("{not-valid-json")
    monkeypatch.setattr(
        "cit.core.keychain.read_keychain_payload",
        lambda: {"claudeAiOauth": {"subscriptionType": "max"}},
    )

    from cit.cli import main

    result = runner.invoke(main, ["status", "--short"])

    assert result.exit_code == 0
    assert wal_file.exists() is False
