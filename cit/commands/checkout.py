from __future__ import annotations

import click

from cit.core import keychain
from cit.core.claude_files import (
    merge_mcp,
    merge_settings,
    patch_oauth_account,
    read_mcp,
    read_oauth_account,
    read_settings,
)
from cit.core.config_manager import resolve_config
from cit.core.lock import cit_lock
from cit.core.profile import create_stash_entry, load_profile, save_current_profile
from cit.core.state import push_stash_id, read_state, set_active_profile
from cit.core.wal import clear_wal, recover_if_needed, update_wal_step, write_wal


@click.command()
@click.option(
    "-b",
    "create_name",
    default=None,
    help="Create a profile from the current state and switch to it",
)
@click.argument("name", required=False)
def checkout(create_name: str | None, name: str | None) -> None:
    with cit_lock():
        recover_if_needed()
        state = read_state()
        current = state.get("activeProfile")
        if create_name:
            save_current_profile(create_name, with_config=True)
            set_active_profile(create_name, current)
            click.echo(f"Switched to a new profile '{create_name}'")
            return
        if name is None:
            raise click.ClickException("A profile name is required")
        if name == "-":
            name = state.get("previousProfile")
            if name is None:
                raise click.ClickException("No previous profile")
        target = load_profile(name)
        keychain.validate_keychain_access()
        config = resolve_config(current)
        if config.get("auto-stash", True):
            stash_id = create_stash_entry(
                message=f"auto: pre-checkout from {current or 'detached'}"
            )
            push_stash_id(stash_id)
        backup = {
            "keychain": keychain.read_keychain_payload(),
            "oauth_account": read_oauth_account(),
            "settings": read_settings(),
            "mcp": read_mcp(),
        }
        write_wal(
            {"op": "checkout", "from": current, "to": name, "step": 0, "backup": backup}
        )
        try:
            keychain.write_keychain_payload(target["keychain"])
            update_wal_step(1)
            patch_oauth_account(target["oauth_account"])
            update_wal_step(2)
            if target.get("settings"):
                merge_settings(target["settings"])
            update_wal_step(3)
            if target.get("mcp"):
                merge_mcp(target["mcp"])
            clear_wal()
        except Exception as error:
            recover_if_needed()
            raise click.ClickException(str(error)) from error
        set_active_profile(name, current)
        click.echo(f"Switched to profile '{name}'")
