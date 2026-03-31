from __future__ import annotations

import json
import re
import shutil
import time
from pathlib import Path
from typing import Any

from cit.core import keychain
from cit.core.claude_files import read_mcp, read_oauth_account, read_settings
from cit.core.state import ensure_cit_dirs


PROFILE_PATTERN = re.compile(r"^[a-z0-9][a-z0-9_-]{0,31}$")


def profiles_dir() -> Path:
    return ensure_cit_dirs() / "profiles"


def stash_dir() -> Path:
    return ensure_cit_dirs() / "stash"


def _write_snapshot_file(
    path: Path, payload: dict[str, Any], mode: int = 0o600
) -> None:
    path.write_text(json.dumps(payload, indent=2))
    path.chmod(mode)


def _ensure_private_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)
    path.chmod(0o700)


def validate_profile_name(name: str) -> None:
    if name == "HEAD" or not PROFILE_PATTERN.match(name):
        raise ValueError("Invalid profile name")


def profile_path(name: str) -> Path:
    return profiles_dir() / name


def list_profiles() -> list[str]:
    return sorted(path.name for path in profiles_dir().iterdir() if path.is_dir())


def load_snapshot(path: Path) -> dict[str, Any]:
    snapshot: dict[str, Any] = {
        "keychain": json.loads((path / "keychain.json").read_text()),
        "oauth_account": json.loads((path / "oauth_account.json").read_text()),
        "meta": json.loads((path / "meta.json").read_text()),
    }
    if (path / "settings.json").exists():
        snapshot["settings"] = json.loads((path / "settings.json").read_text())
    if (path / "mcp.json").exists():
        snapshot["mcp"] = json.loads((path / "mcp.json").read_text())
    return snapshot


def load_profile(name: str) -> dict[str, Any]:
    path = profile_path(name)
    if not path.exists():
        raise FileNotFoundError(f"Profile not found: {name}")
    return load_snapshot(path)


def save_current_profile(name: str, with_config: bool = False) -> Path:
    validate_profile_name(name)
    target = profile_path(name)
    _ensure_private_dir(target)
    keychain_payload = keychain.read_keychain_payload()
    oauth = read_oauth_account()
    settings = read_settings()
    mcp = read_mcp()
    _write_snapshot_file(target / "keychain.json", keychain_payload)
    _write_snapshot_file(target / "oauth_account.json", oauth)
    if with_config and settings:
        _write_snapshot_file(target / "settings.json", settings)
        if mcp:
            _write_snapshot_file(target / "mcp.json", mcp)
    meta = {
        "name": name,
        "createdAt": int(time.time() * 1000),
        "lastUsedAt": None,
        "sourceEmail": oauth.get("emailAddress"),
        "sourceOrganization": oauth.get("organizationName"),
    }
    _write_snapshot_file(target / "meta.json", meta)
    return target


def delete_profile(name: str) -> None:
    path = profile_path(name)
    if not path.exists():
        raise FileNotFoundError(f"Profile not found: {name}")
    shutil.rmtree(path)


def create_stash_entry(message: str | None = None, include_config: bool = True) -> str:
    stash_id = str(int(time.time() * 1000))
    path = stash_dir() / stash_id
    _ensure_private_dir(path)
    keychain_payload = keychain.read_keychain_payload()
    oauth = read_oauth_account()
    settings = read_settings()
    mcp = read_mcp()
    _write_snapshot_file(path / "keychain.json", keychain_payload)
    _write_snapshot_file(path / "oauth_account.json", oauth)
    if include_config and settings:
        _write_snapshot_file(path / "settings.json", settings)
        if mcp:
            _write_snapshot_file(path / "mcp.json", mcp)
    meta = {
        "message": message,
        "createdAt": int(time.time() * 1000),
        "sourceEmail": oauth.get("emailAddress"),
        "subscriptionType": keychain_payload.get("claudeAiOauth", {}).get(
            "subscriptionType"
        ),
    }
    _write_snapshot_file(path / "meta.json", meta)
    return stash_id


def load_stash_entry(stash_id: str) -> dict[str, Any]:
    path = stash_dir() / stash_id
    if not path.exists():
        raise FileNotFoundError(f"Stash not found: {stash_id}")
    return load_snapshot(path)


def delete_stash_entry(stash_id: str) -> None:
    path = stash_dir() / stash_id
    if path.exists():
        shutil.rmtree(path)
