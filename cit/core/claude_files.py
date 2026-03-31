from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from cit.core.paths import get_claude_home, get_claude_json_path


def _read_json(path: Path, default: dict[str, Any] | None = None) -> dict[str, Any]:
    if not path.exists():
        return {} if default is None else default.copy()
    return json.loads(path.read_text())


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2))


def read_claude_json() -> dict[str, Any]:
    return _read_json(get_claude_json_path(), default={})


def patch_oauth_account(oauth_account: dict[str, Any]) -> None:
    payload = read_claude_json()
    payload["oauthAccount"] = oauth_account
    _write_json(get_claude_json_path(), payload)


def read_oauth_account() -> dict[str, Any]:
    return read_claude_json().get("oauthAccount", {})


def settings_path() -> Path:
    return get_claude_home() / "settings.json"


def mcp_path() -> Path:
    return get_claude_home() / ".mcp.json"


def read_settings() -> dict[str, Any]:
    return _read_json(settings_path(), default={})


def write_settings(payload: dict[str, Any]) -> None:
    _write_json(settings_path(), payload)


def merge_settings(overrides: dict[str, Any]) -> None:
    payload = read_settings()
    payload.update(overrides)
    write_settings(payload)


def read_mcp() -> dict[str, Any]:
    return _read_json(mcp_path(), default={})


def write_mcp(payload: dict[str, Any]) -> None:
    _write_json(mcp_path(), payload)


def merge_mcp(overrides: dict[str, Any]) -> None:
    payload = read_mcp()
    payload.update(overrides)
    write_mcp(payload)
