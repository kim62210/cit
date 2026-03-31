from __future__ import annotations

import json
from pathlib import Path

import click

from cit.core.pricing import estimate_cost
from cit.core.session_reader import read_sessions


@click.command(name="log")
@click.option("--today", "today_only", is_flag=True, help="Show only today's sessions")
@click.option(
    "--week", "week_only", is_flag=True, help="Show only this week's sessions"
)
@click.option("--project", "project_path", default=None, help="Filter by project path")
@click.option(
    "--stats", "show_stats", is_flag=True, help="Show aggregate token usage and cost"
)
@click.option("--json", "json_output", is_flag=True, help="Show machine-readable JSON")
def log_command(
    today_only: bool,
    week_only: bool,
    project_path: str | None,
    show_stats: bool,
    json_output: bool,
) -> None:
    window = "today" if today_only else "week" if week_only else None
    sessions = read_sessions(
        window=window, project_filter=Path(project_path) if project_path else None
    )
    if json_output:
        click.echo(json.dumps([entry.model_dump() for entry in sessions], indent=2))
        return
    total_input = 0
    total_output = 0
    total_cost = 0.0
    for entry in sessions[:20]:
        usage = entry.usage
        total_input += (
            usage.input_tokens
            + usage.cache_read_input_tokens
            + usage.cache_creation_input_tokens
        )
        total_output += usage.output_tokens
        total_cost += estimate_cost(
            entry.model, usage.input_tokens, usage.output_tokens
        )
        click.echo(f"{entry.started_at}  {entry.project_slug}")
        click.echo(
            f"  {entry.session_id}  {entry.model or 'unknown'}  in:{usage.input_tokens:,}  out:{usage.output_tokens:,}  cache_read:{usage.cache_read_input_tokens:,}"
        )
        click.echo("")
    if show_stats:
        click.echo(
            f"-- Total: {len(sessions)} sessions, {total_input:,} input tokens, {total_output:,} output tokens --"
        )
        click.echo(f"-- Est. cost: ${total_cost:.2f} --")
