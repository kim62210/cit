from __future__ import annotations

from contextlib import contextmanager

from cit.cli import main
from cit.core.state import set_active_profile


def test_main_runs_recovery_inside_lock(runner, monkeypatch):
    events: list[str] = []

    @contextmanager
    def fake_lock():
        events.append("lock-enter")
        try:
            yield
        finally:
            events.append("lock-exit")

    monkeypatch.setattr("cit.cli.cit_lock", fake_lock)
    monkeypatch.setattr("cit.cli.recover_if_needed", lambda: events.append("recover"))
    monkeypatch.setattr(
        "cit.core.keychain.read_keychain_payload",
        lambda: {"claudeAiOauth": {"subscriptionType": "max"}},
    )

    result = runner.invoke(main, ["status", "--short"])

    assert result.exit_code == 0
    assert events == ["lock-enter", "recover", "lock-exit"]


def test_config_set_uses_lock(runner, env_paths, monkeypatch):
    events: list[str] = []

    @contextmanager
    def fake_lock():
        events.append("lock-enter")
        try:
            yield
        finally:
            events.append("lock-exit")

    monkeypatch.setattr("cit.commands.config.cit_lock", fake_lock)
    monkeypatch.setattr(
        "cit.core.keychain.read_keychain_payload",
        lambda: {"claudeAiOauth": {"subscriptionType": "max"}},
    )
    set_active_profile("work", None)

    result = runner.invoke(main, ["config", "model", "opus[1m]"])

    assert result.exit_code == 0
    assert events == ["lock-enter", "lock-exit"]


def test_stash_push_uses_lock(runner, env_paths, monkeypatch):
    events: list[str] = []

    @contextmanager
    def fake_lock():
        events.append("lock-enter")
        try:
            yield
        finally:
            events.append("lock-exit")

    monkeypatch.setattr("cit.commands.stash.cit_lock", fake_lock)
    monkeypatch.setattr(
        "cit.core.keychain.read_keychain_payload",
        lambda: {"claudeAiOauth": {"subscriptionType": "max"}},
    )

    result = runner.invoke(main, ["stash"])

    assert result.exit_code == 0
    assert events == ["lock-enter", "lock-exit"]
