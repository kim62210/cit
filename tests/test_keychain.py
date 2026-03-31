from __future__ import annotations

import pytest

from cit.platform.macos import MacOSKeychainStore


def test_keychain_store_read_parses_json(monkeypatch):
    monkeypatch.setattr(
        MacOSKeychainStore,
        "_run",
        lambda self, *args, **kwargs: type(
            "Completed",
            (),
            {
                "returncode": 0,
                "stdout": '{"claudeAiOauth": {"subscriptionType": "max"}}',
                "stderr": "",
            },
        )(),
    )

    payload = MacOSKeychainStore().read()

    assert payload["claudeAiOauth"]["subscriptionType"] == "max"


def test_keychain_store_write_handles_delete_missing_and_add_success(monkeypatch):
    calls: list[tuple[str, ...]] = []

    def fake_run(self, *args, **kwargs):
        calls.append(args)
        return type(
            "Completed",
            (),
            {
                "returncode": 44 if args[0] == "delete-generic-password" else 0,
                "stdout": "",
                "stderr": "",
            },
        )()

    monkeypatch.setattr(MacOSKeychainStore, "_run", fake_run)

    MacOSKeychainStore().write({"claudeAiOauth": {"subscriptionType": "max"}})

    assert calls[0][0] == "delete-generic-password"
    assert calls[1][0] == "add-generic-password"


def test_keychain_store_delete_and_validate_raise_on_failure(monkeypatch):
    monkeypatch.setattr(
        MacOSKeychainStore,
        "_run",
        lambda self, *args, **kwargs: type(
            "Completed", (), {"returncode": 1, "stdout": "", "stderr": "boom"}
        )(),
    )

    with pytest.raises(RuntimeError, match="boom"):
        MacOSKeychainStore().delete()

    with pytest.raises(RuntimeError, match="boom"):
        MacOSKeychainStore().validate_access()
