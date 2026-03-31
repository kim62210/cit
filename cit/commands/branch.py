from __future__ import annotations

import click

from cit.core.profile import (
    delete_profile,
    list_profiles,
    load_profile,
    save_current_profile,
)
from cit.core.state import read_state


@click.command(context_settings={"ignore_unknown_options": True})
@click.argument("name", required=False)
@click.option("-d", "delete_name", default=None, help="Delete profile")
@click.option("-v", "verbose", is_flag=True, help="Verbose output")
@click.option(
    "--with-config", is_flag=True, help="Include Claude settings and MCP files"
)
def branch(
    name: str | None, delete_name: str | None, verbose: bool, with_config: bool
) -> None:
    state = read_state()
    active = state.get("activeProfile")
    if delete_name:
        delete_profile(delete_name)
        click.echo(f"Deleted profile {delete_name}")
        return
    if name:
        save_current_profile(name, with_config=with_config)
        click.echo(f"Saved current account as {name}")
        return
    for profile_name in list_profiles():
        marker = "*" if profile_name == active else " "
        if not verbose:
            click.echo(f"{marker} {profile_name}")
            continue
        snapshot = load_profile(profile_name)
        oauth = snapshot["oauth_account"]
        subscription = (
            snapshot["keychain"]
            .get("claudeAiOauth", {})
            .get("subscriptionType", "unknown")
        )
        rate_limit = snapshot["keychain"].get("claudeAiOauth", {}).get("rateLimitTier")
        suffix = f" ({rate_limit})" if rate_limit else ""
        click.echo(
            f"{marker} {profile_name:<16} {oauth.get('emailAddress', 'unknown'):<28} {subscription}{suffix}"
        )
