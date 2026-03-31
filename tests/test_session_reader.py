from __future__ import annotations

import json
from pathlib import Path

from cit.core.session_reader import project_slug_for_path, read_sessions


def test_session_reader_returns_empty_for_missing_project(env_paths):
    sessions = read_sessions(project_filter=Path("/tmp/does-not-exist"))

    assert sessions == []


def test_session_reader_skips_files_without_assistant_usage(env_paths):
    project_path = Path("/tmp/no-usage-project")
    project_dir = env_paths["projects_home"] / project_slug_for_path(project_path)
    project_dir.mkdir(parents=True, exist_ok=True)
    (project_dir / "session-a.jsonl").write_text(
        "\n".join(
            [
                json.dumps(
                    {
                        "created_at": "2026-03-31T10:00:00Z",
                        "message": {"role": "assistant"},
                    }
                ),
                json.dumps(
                    {"created_at": "2026-03-31T10:01:00Z", "message": {"role": "user"}}
                ),
            ]
        )
    )

    sessions = read_sessions(project_filter=project_path)

    assert sessions == []


def test_session_reader_filters_today_and_week_windows(env_paths):
    project_path = Path("/tmp/window-project")
    project_dir = env_paths["projects_home"] / project_slug_for_path(project_path)
    project_dir.mkdir(parents=True, exist_ok=True)
    (project_dir / "today.jsonl").write_text(
        json.dumps(
            {
                "created_at": "2026-03-31T10:56:00Z",
                "message": {
                    "role": "assistant",
                    "model": "claude-opus-4-6",
                    "usage": {"input_tokens": 1, "output_tokens": 2},
                },
            }
        )
    )
    (project_dir / "old.jsonl").write_text(
        json.dumps(
            {
                "created_at": "2026-03-01T10:56:00Z",
                "message": {
                    "role": "assistant",
                    "model": "claude-opus-4-6",
                    "usage": {"input_tokens": 3, "output_tokens": 4},
                },
            }
        )
    )

    today_sessions = read_sessions(window="today", project_filter=project_path)
    week_sessions = read_sessions(window="week", project_filter=project_path)

    assert [entry.session_id for entry in today_sessions] == ["today"]
    assert [entry.session_id for entry in week_sessions] == ["today"]
