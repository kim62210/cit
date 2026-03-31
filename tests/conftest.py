from __future__ import annotations

import json
from pathlib import Path

import pytest
from click.testing import CliRunner


@pytest.fixture()
def runner() -> CliRunner:
    return CliRunner()


@pytest.fixture()
def env_paths(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> dict[str, Path]:
    cit_home = tmp_path / ".cit"
    claude_home = tmp_path / ".claude"
    claude_json = tmp_path / ".claude.json"
    projects_home = claude_home / "projects"
    monkeypatch.setenv("CIT_HOME", str(cit_home))
    monkeypatch.setenv("CLAUDE_HOME", str(claude_home))
    monkeypatch.setenv("CLAUDE_JSON_PATH", str(claude_json))
    monkeypatch.setenv("CLAUDE_PROJECTS_HOME", str(projects_home))
    claude_home.mkdir(parents=True, exist_ok=True)
    projects_home.mkdir(parents=True, exist_ok=True)
    claude_json.write_text(
        json.dumps(
            {
                "installMethod": "test",
                "oauthAccount": {
                    "emailAddress": "active@example.com",
                    "displayName": "Active",
                    "organizationName": "Example Org",
                    "organizationRole": "member",
                },
            }
        )
    )
    (claude_home / "settings.json").write_text(json.dumps({"model": "opus"}))
    return {
        "cit_home": cit_home,
        "claude_home": claude_home,
        "claude_json": claude_json,
        "projects_home": projects_home,
    }
