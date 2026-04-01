from __future__ import annotations

import time
from contextlib import contextmanager

import pytest

from cit.cli import main
from cit.core.lock import LockTimeoutError, cit_lock, is_lock_held
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


def test_is_lock_held_returns_false_when_no_lock_file(env_paths):
    assert is_lock_held() is False


def test_is_lock_held_returns_false_when_lock_not_held(env_paths):
    from cit.core.paths import get_cit_home

    lock_path = get_cit_home() / ".lock"
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    lock_path.touch()
    assert is_lock_held() is False


def test_cit_lock_acquires_lock_successfully(env_paths):
    with cit_lock(timeout=1.0):
        assert is_lock_held() is True


def test_cit_lock_raises_timeout_error_when_blocked(env_paths, monkeypatch):
    from cit.core.paths import get_cit_home

    lock_path = get_cit_home() / ".lock"
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    lock_path.touch()

    def long_running_lock():
        with cit_lock(timeout=30.0):
            time.sleep(10.0)

    import threading

    thread = threading.Thread(target=long_running_lock)
    thread.start()
    time.sleep(0.2)

    with pytest.raises(LockTimeoutError) as exc_info:
        with cit_lock(timeout=0.5):
            pass
    assert "Could not acquire lock" in str(exc_info.value)
    assert "Another cit process may be running" in str(exc_info.value)

    thread.join(timeout=15.0)


def test_cit_lock_timeout_zero_raises_immediately(env_paths, monkeypatch):
    from cit.core.paths import get_cit_home

    lock_path = get_cit_home() / ".lock"
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    lock_path.touch()

    def long_running_lock():
        with cit_lock(timeout=30.0):
            time.sleep(10.0)

    import threading

    thread = threading.Thread(target=long_running_lock)
    thread.start()
    time.sleep(0.2)

    with pytest.raises(LockTimeoutError):
        with cit_lock(timeout=0.0):
            pass

    thread.join(timeout=15.0)
