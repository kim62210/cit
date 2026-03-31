from __future__ import annotations

import json
from pathlib import Path

from cit.cli import main
from cit.core.session_reader import project_slug_for_path
from cit.core.state import set_active_profile, push_stash_id


def test_status_short_shows_profile_account_and_model(runner, env_paths, monkeypatch):
    monkeypatch.setattr(
        "cit.core.keychain.read_keychain_payload",
        lambda: {
            "claudeAiOauth": {
                "subscriptionType": "max",
                "rateLimitTier": "default_claude_max_20x",
                "expiresAt": 4102444800000,
            }
        },
    )
    set_active_profile("work", "personal")
    push_stash_id("12345")

    result = runner.invoke(main, ["status", "--short"])

    assert result.exit_code == 0
    assert "work active@example.com max opus" in result.output


def test_status_full_shows_recent_session_summary(runner, env_paths, monkeypatch):
    monkeypatch.setattr(
        "cit.core.keychain.read_keychain_payload",
        lambda: {
            "claudeAiOauth": {
                "subscriptionType": "max",
                "rateLimitTier": "default_claude_max_20x",
                "expiresAt": 4102444800000,
            }
        },
    )
    project_path = Path("/tmp/sample-project")
    project_dir = env_paths["projects_home"] / project_slug_for_path(project_path)
    project_dir.mkdir(parents=True, exist_ok=True)
    (project_dir / "session-1.jsonl").write_text(
        "\n".join(
            [
                json.dumps(
                    {"created_at": "2026-03-31T10:55:00Z", "message": {"role": "user"}}
                ),
                json.dumps(
                    {
                        "created_at": "2026-03-31T10:56:00Z",
                        "message": {
                            "role": "assistant",
                            "model": "claude-opus-4-6",
                            "usage": {
                                "input_tokens": 23269,
                                "output_tokens": 131,
                                "cache_read_input_tokens": 10482,
                            },
                        },
                    }
                ),
            ]
        )
    )

    result = runner.invoke(main, ["status"])

    assert result.exit_code == 0
    assert "Session:       recent session-1 (claude-opus-4-6)" in result.output


def test_status_json_shows_machine_readable_payload(runner, env_paths, monkeypatch):
    monkeypatch.setattr(
        "cit.core.keychain.read_keychain_payload",
        lambda: {
            "claudeAiOauth": {
                "subscriptionType": "max",
                "rateLimitTier": "default_claude_max_20x",
                "expiresAt": 4102444800000,
            }
        },
    )
    set_active_profile("work", "personal")
    push_stash_id("12345")
    project_path = Path("/tmp/sample-project")
    project_dir = env_paths["projects_home"] / project_slug_for_path(project_path)
    project_dir.mkdir(parents=True, exist_ok=True)
    (project_dir / "session-1.jsonl").write_text(
        "\n".join(
            [
                json.dumps(
                    {"created_at": "2026-03-31T10:55:00Z", "message": {"role": "user"}}
                ),
                json.dumps(
                    {
                        "created_at": "2026-03-31T10:56:00Z",
                        "message": {
                            "role": "assistant",
                            "model": "claude-opus-4-6",
                            "usage": {
                                "input_tokens": 23269,
                                "output_tokens": 131,
                                "cache_read_input_tokens": 10482,
                            },
                        },
                    }
                ),
            ]
        )
    )

    result = runner.invoke(main, ["status", "--json"])

    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert payload["profile"] == "work"
    assert payload["account"] == "active@example.com"
    assert payload["subscription"] == "max"
    assert payload["model"] == "opus"
    assert payload["stash_count"] == 1
    assert payload["session"]["session_id"] == "session-1"
    assert payload["session"]["model"] == "claude-opus-4-6"
