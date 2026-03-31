from __future__ import annotations

from typing import Any

from cit.platform.macos import MacOSKeychainStore


def get_store() -> MacOSKeychainStore:
    return MacOSKeychainStore()


def read_keychain_payload() -> dict[str, Any]:
    return get_store().read()


def write_keychain_payload(payload: dict[str, Any]) -> None:
    get_store().write(payload)


def validate_keychain_access() -> None:
    get_store().validate_access()
