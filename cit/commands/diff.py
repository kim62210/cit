from __future__ import annotations

import click

from cit.core.context_diff import render_context_diff


@click.command(
    name="diff",
    help="Compare two saved Claude contexts stored as profiles.",
    short_help="Compare two saved Claude contexts.",
)
@click.argument("from_name")
@click.argument("to_name")
def diff_command(from_name: str, to_name: str) -> None:
    try:
        click.echo(render_context_diff(from_name, to_name))
    except FileNotFoundError as error:
        raise click.ClickException(str(error)) from error
