from __future__ import annotations

import json
from datetime import datetime, timezone

import click

from cit.core import keychain
from cit.core.claude_files import merge_mcp, merge_settings, patch_oauth_account
from cit.core.lock import cit_lock
from cit.core.profile import create_stash_entry, delete_stash_entry, load_stash_entry
from cit.core.state import pop_stash_id, push_stash_id, read_state


def _get_stash_id(index: int) -> str:
    stack = read_state().get("stashStack", [])
    if index >= len(stack):
        raise click.ClickException("Stash index out of range")
    return stack[index]


@click.group(
    invoke_without_command=True,
    help="Temporarily save, inspect, restore, and drop local context snapshots.",
    short_help="Temporarily save and restore context state.",
)
@click.pass_context
def stash(ctx: click.Context) -> None:
    if ctx.invoked_subcommand is None:
        with cit_lock():
            stash_id = create_stash_entry(message="manual stash")
            push_stash_id(stash_id)
        click.echo(f"Saved stash@{{0}}: {stash_id}")


@stash.command("list")
def list_stash() -> None:
    for index, stash_id in enumerate(read_state().get("stashStack", [])):
        entry = load_stash_entry(stash_id)
        meta = entry["meta"]
        created_at = datetime.fromtimestamp(
            meta["createdAt"] / 1000, tz=timezone.utc
        ).strftime("%Y-%m-%d %H:%M")
        email = entry["oauth_account"].get("emailAddress", "unknown")
        subscription = (
            entry["keychain"]
            .get("claudeAiOauth", {})
            .get("subscriptionType", "unknown")
        )
        message = meta.get("message") or email
        click.echo(
            f"stash@{{{index}}}: {message} - {email} ({subscription}) [{created_at}]"
        )


@stash.command("show")
@click.argument("index", required=False, default="0")
def show_stash(index: str) -> None:
    stash_id = _get_stash_id(int(index))
    click.echo(json.dumps(load_stash_entry(stash_id), indent=2))


@stash.command("drop")
@click.argument("index", required=False, default="0")
def drop_stash(index: str) -> None:
    with cit_lock():
        stash_id = pop_stash_id(int(index))
        delete_stash_entry(stash_id)
    click.echo(f"Dropped stash@{{{index}}}")


@stash.command("pop")
@click.argument("index", required=False, default="0")
def pop_stash(index: str) -> None:
    stash_index = int(index)
    with cit_lock():
        stash_id = _get_stash_id(stash_index)
        entry = load_stash_entry(stash_id)
        keychain.write_keychain_payload(entry["keychain"])
        patch_oauth_account(entry["oauth_account"])
        if entry.get("settings"):
            merge_settings(entry["settings"])
        if entry.get("mcp"):
            merge_mcp(entry["mcp"])
        pop_stash_id(stash_index)
        delete_stash_entry(stash_id)
    click.echo(f"Applied stash@{{{stash_index}}}")
