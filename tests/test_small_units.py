from __future__ import annotations

import json
from abc import ABC

import pytest

from cit.core.claude_files import patch_oauth_account, read_claude_json
from cit.core.paths import (
    get_claude_home,
    get_claude_json_path,
    get_claude_projects_home,
    get_cit_home,
)
from cit.core.pricing import estimate_cost
from cit.core.state import pop_stash_id, push_stash_id, read_state
from cit.core.wal import recover_if_needed, write_wal
from cit.platform.base import CredentialStore


def test_paths_use_environment_overrides(env_paths):
    assert get_cit_home() == env_paths["cit_home"]
    assert get_claude_home() == env_paths["claude_home"]
    assert get_claude_json_path() == env_paths["claude_json"]
    assert get_claude_projects_home() == env_paths["projects_home"]


def test_pricing_falls_back_for_unknown_models():
    assert estimate_cost(None, 1_000_000, 0) == 15.0
    assert estimate_cost("unknown-model", 0, 1_000_000) == 75.0


def test_state_pop_stash_raises_for_invalid_index(env_paths):
    push_stash_id("one")

    with pytest.raises(IndexError, match="stash index out of range"):
        pop_stash_id(1)

    assert read_state()["stashStack"] == ["one"]


def test_wal_recovery_restores_backups(env_paths, monkeypatch):
    restored: dict[str, object] = {}
    write_wal(
        {
            "op": "checkout",
            "step": 2,
            "backup": {
                "keychain": {"claudeAiOauth": {"subscriptionType": "max"}},
                "oauth_account": {"emailAddress": "restore@example.com"},
                "settings": {"model": "opus"},
                "mcp": {"memory": {"command": "npx"}},
            },
        }
    )
    monkeypatch.setattr(
        "cit.core.keychain.write_keychain_payload",
        lambda payload: restored.__setitem__("keychain", payload),
    )

    recover_if_needed()

    assert restored["keychain"] == {"claudeAiOauth": {"subscriptionType": "max"}}
    assert json.loads(env_paths["claude_json"].read_text())["oauthAccount"] == {
        "emailAddress": "restore@example.com"
    }
    assert json.loads((env_paths["claude_home"] / "settings.json").read_text()) == {
        "model": "opus"
    }
    assert json.loads((env_paths["claude_home"] / ".mcp.json").read_text()) == {
        "memory": {"command": "npx"}
    }


def test_patch_oauth_account_preserves_other_claude_json_fields(env_paths):
    patch_oauth_account({"emailAddress": "patched@example.com"})

    payload = read_claude_json()

    assert payload["installMethod"] == "test"
    assert payload["oauthAccount"]["emailAddress"] == "patched@example.com"


def test_credential_store_cannot_be_instantiated_directly():
    with pytest.raises(TypeError):
        CredentialStore()

    class DerivedStore(CredentialStore, ABC):
        pass

    with pytest.raises(TypeError):
        DerivedStore()
