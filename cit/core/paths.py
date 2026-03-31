from __future__ import annotations

import os
from pathlib import Path


def get_cit_home() -> Path:
    return Path(os.environ.get("CIT_HOME", Path.home() / ".cit")).expanduser()


def get_claude_home() -> Path:
    return Path(os.environ.get("CLAUDE_HOME", Path.home() / ".claude")).expanduser()


def get_claude_json_path() -> Path:
    return Path(
        os.environ.get("CLAUDE_JSON_PATH", Path.home() / ".claude.json")
    ).expanduser()


def get_claude_projects_home() -> Path:
    return Path(
        os.environ.get("CLAUDE_PROJECTS_HOME", get_claude_home() / "projects")
    ).expanduser()
