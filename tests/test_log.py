from __future__ import annotations

import json
from pathlib import Path

from cit.cli import main
from cit.core.session_reader import project_slug_for_path


def test_log_stats_reads_usage_from_session_jsonl(runner, env_paths):
    project_path = Path("/tmp/sample-project")
    project_dir = env_paths["projects_home"] / project_slug_for_path(project_path)
    project_dir.mkdir(parents=True, exist_ok=True)
    session_file = project_dir / "session-1.jsonl"
    session_file.write_text(
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

    result = runner.invoke(main, ["log", "--project", str(project_path), "--stats"])

    assert result.exit_code == 0
    assert "session-1" in result.output
    assert "Total: 1 sessions" in result.output
    assert "Est. cost:" in result.output
