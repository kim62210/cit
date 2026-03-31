from __future__ import annotations

import json
from datetime import date, datetime, timedelta
from pathlib import Path

from cit.core.paths import get_claude_projects_home
from cit.models.session import SessionEntry, TokenUsage


def project_slug_for_path(project_path: Path) -> str:
    return str(project_path.resolve()).replace("/", "-").replace(":", "")


def _iter_session_files(project_filter: Path | None) -> list[Path]:
    base = get_claude_projects_home()
    if not base.exists():
        return []
    if project_filter is not None:
        target = base / project_slug_for_path(project_filter)
        return sorted(target.glob("*.jsonl")) if target.exists() else []
    return sorted(base.glob("*/*.jsonl"))


def _matches_window(timestamp: datetime, window: str | None) -> bool:
    today = date.today()
    if window == "today":
        return timestamp.date() == today
    if window == "week":
        return timestamp.date() >= today - timedelta(days=today.weekday())
    return True


def read_sessions(
    window: str | None = None, project_filter: Path | None = None
) -> list[SessionEntry]:
    entries: list[SessionEntry] = []
    for path in _iter_session_files(project_filter):
        usage = TokenUsage()
        model = None
        started_at = None
        with path.open() as handle:
            for raw_line in handle:
                line = json.loads(raw_line)
                message = line.get("message", {})
                if message.get("role") != "assistant":
                    continue
                usage_payload = message.get("usage")
                if not usage_payload:
                    continue
                usage = TokenUsage.model_validate(usage_payload)
                model = message.get("model") or model
                started_at = line.get("created_at") or started_at
                break
        if started_at is None:
            continue
        timestamp = datetime.fromisoformat(started_at.replace("Z", "+00:00"))
        if not _matches_window(timestamp, window):
            continue
        entries.append(
            SessionEntry(
                session_id=path.stem,
                project_slug=path.parent.name,
                model=model,
                started_at=started_at,
                usage=usage,
            )
        )
    return sorted(entries, key=lambda item: item.started_at or "", reverse=True)
