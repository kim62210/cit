from __future__ import annotations

import json

import click

from cit.core.config_manager import (
    get_config_value,
    list_profile_config,
    set_config_value,
    unset_config_value,
)
from cit.core.lock import cit_lock
from cit.core.state import read_state


@click.command(
    help="Inspect and update global or per-profile cit configuration.",
    short_help="Manage cit configuration.",
)
@click.option("--list", "list_values", is_flag=True, help="List config values")
@click.option("--global", "global_scope", is_flag=True, help="Use global scope")
@click.option("--unset", "unset_key", default=None, help="Unset key")
@click.argument("key", required=False)
@click.argument("value", required=False)
def config(
    list_values: bool,
    global_scope: bool,
    unset_key: str | None,
    key: str | None,
    value: str | None,
) -> None:
    active_profile = read_state().get("activeProfile")
    if list_values:
        click.echo(
            json.dumps(list_profile_config(active_profile), indent=2, sort_keys=True)
        )
        return
    if unset_key:
        if not active_profile:
            raise click.ClickException("No active profile")
        with cit_lock():
            unset_config_value(unset_key, active_profile)
        click.echo(f"Unset {unset_key}")
        return
    if key is None:
        raise click.ClickException("A key is required")
    if value is None:
        current = get_config_value(key, active_profile)
        click.echo(json.dumps(current) if isinstance(current, dict) else current)
        return
    with cit_lock():
        set_config_value(key, value, active_profile, global_scope=global_scope)
    click.echo(f"Set {key}")
