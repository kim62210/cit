from __future__ import annotations

import json

import click

from cit.core.context_diff import context_diff_payload, render_context_diff


@click.command(
    name="diff",
    help="Compare two saved Claude contexts stored as profiles.",
    short_help="Compare two saved Claude contexts.",
)
@click.option(
    "--json", "json_output", is_flag=True, help="Show machine-readable JSON output"
)
@click.argument("from_name")
@click.argument("to_name")
def diff_command(from_name: str, to_name: str, json_output: bool) -> None:
    try:
        if json_output:
            click.echo(
                json.dumps(
                    context_diff_payload(from_name, to_name), indent=2, sort_keys=True
                )
            )
            return
        click.echo(render_context_diff(from_name, to_name))
    except FileNotFoundError as error:
        raise click.ClickException(str(error)) from error
