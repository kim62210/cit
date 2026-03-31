from __future__ import annotations

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
