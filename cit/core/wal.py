from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from cit.core import keychain
from cit.core.claude_files import patch_oauth_account, write_mcp, write_settings
from cit.core.state import ensure_cit_dirs


def wal_path() -> Path:
    return ensure_cit_dirs() / "wal.json"


def write_wal(payload: dict[str, Any]) -> None:
    wal_path().write_text(json.dumps(payload, indent=2))


def read_wal() -> dict[str, Any] | None:
    path = wal_path()
    if not path.exists():
        return None
    payload = json.loads(path.read_text())
    return payload if payload else None


def clear_wal() -> None:
    path = wal_path()
    if path.exists():
        path.unlink()


def update_wal_step(step: int) -> None:
    payload = read_wal()
    if payload is None:
        return
    payload["step"] = step
    write_wal(payload)


def recover_if_needed() -> None:
    payload = read_wal()
    if not payload:
        return
    backup = payload.get("backup", {})
    if backup.get("keychain") is not None:
        keychain.write_keychain_payload(backup["keychain"])
    if backup.get("oauth_account") is not None:
        patch_oauth_account(backup["oauth_account"])
    if backup.get("settings") is not None:
        write_settings(backup["settings"])
    if backup.get("mcp") is not None:
        write_mcp(backup["mcp"])
    clear_wal()
