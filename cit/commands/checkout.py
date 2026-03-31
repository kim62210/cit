from __future__ import annotations

import subprocess
from typing import Any

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
from cit.core.config_manager import checkout_overrides, resolve_config
from cit.core.lock import cit_lock
from cit.core.profile import create_stash_entry, load_profile, save_current_profile
from cit.core.state import push_stash_id, read_state, set_active_profile
from cit.core.wal import clear_wal, recover_if_needed, update_wal_step, write_wal


def _has_unsaved_changes(current: str | None) -> bool:
    if current is None:
        return True
    try:
        current_profile = load_profile(current)
    except FileNotFoundError:
        return True
    live_keychain = keychain.read_keychain_payload()
    live_oauth = read_oauth_account()
    if current_profile["keychain"] != live_keychain:
        return True
    if current_profile["oauth_account"] != live_oauth:
        return True
    live_settings = read_settings()
    if (
        current_profile.get("settings") is not None
        and current_profile["settings"] != live_settings
    ):
        return True
    live_mcp = read_mcp()
    if current_profile.get("mcp") is not None and current_profile["mcp"] != live_mcp:
        return True
    return False


def has_running_claude_process() -> bool:
    result = subprocess.run(
        ["pgrep", "-x", "claude"],
        capture_output=True,
        text=True,
        check=False,
    )
    return result.returncode == 0


def _build_target_settings(
    target: dict[str, Any], settings_overrides: dict[str, Any]
) -> dict[str, Any]:
    target_settings = dict(target.get("settings") or {})
    target_settings.update(settings_overrides)
    return target_settings


def _build_target_mcp(
    target: dict[str, Any], mcp_overrides: dict[str, Any]
) -> dict[str, Any]:
    target_mcp = dict(target.get("mcp") or {})
    target_mcp.update(mcp_overrides)
    return target_mcp


def _describe_mcp_changes(
    current_mcp: dict[str, Any], target_mcp: dict[str, Any]
) -> list[str]:
    changes: list[str] = []
    keys = sorted(set(current_mcp) | set(target_mcp))
    for key in keys:
        if key not in current_mcp:
            changes.append(f"+ mcp.{key}")
        elif key not in target_mcp:
            changes.append(f"- mcp.{key}")
        elif current_mcp[key] != target_mcp[key]:
            changes.append(f"~ mcp.{key}")
    return changes


def _build_checkout_plan(current: str | None, name: str) -> dict[str, Any]:
    target = load_profile(name)
    current_oauth = read_oauth_account()
    current_settings = read_settings()
    current_mcp = read_mcp()
    current_keychain = keychain.read_keychain_payload().get("claudeAiOauth", {})
    settings_overrides, mcp_overrides = checkout_overrides(name)
    target_settings = _build_target_settings(target, settings_overrides)
    target_mcp = _build_target_mcp(target, mcp_overrides)
    warnings: list[str] = []
    if has_running_claude_process():
        warnings.append(
            "Claude appears to be running; switching accounts may disrupt active sessions."
        )
    return {
        "from_profile": current or "detached",
        "to_profile": name,
        "current": {
            "account": current_oauth.get("emailAddress", "unknown"),
            "subscription": current_keychain.get("subscriptionType", "unknown"),
            "model": current_settings.get("model", "unknown"),
            "permission-mode": current_settings.get("permission-mode"),
            "mcp": current_mcp,
        },
        "target": target,
        "target_settings": target_settings,
        "target_mcp": target_mcp,
        "will_auto_stash": resolve_config(current).get("auto-stash", True)
        and _has_unsaved_changes(current),
        "warnings": warnings,
    }


def _render_checkout_plan(plan: dict[str, Any]) -> str:
    target_oauth = plan["target"]["oauth_account"]
    target_keychain = plan["target"]["keychain"].get("claudeAiOauth", {})
    lines = [
        f"Dry run: checkout '{plan['to_profile']}'",
        f"Profile: {plan['from_profile']} -> {plan['to_profile']}",
        f"Account: {plan['current']['account']} -> {target_oauth.get('emailAddress', 'unknown')}",
    ]
    if plan["current"]["subscription"] != target_keychain.get(
        "subscriptionType", "unknown"
    ):
        lines.append(
            f"~ subscription: {plan['current']['subscription']} -> {target_keychain.get('subscriptionType', 'unknown')}"
        )
    if plan["current"]["model"] != plan["target_settings"].get("model", "unknown"):
        lines.append(
            f"~ model: {plan['current']['model']} -> {plan['target_settings'].get('model', 'unknown')}"
        )
    if plan["current"].get("permission-mode") != plan["target_settings"].get(
        "permission-mode"
    ):
        lines.append(
            f"~ permission-mode: {plan['current'].get('permission-mode', 'unset')} -> {plan['target_settings'].get('permission-mode', 'unset')}"
        )
    lines.extend(_describe_mcp_changes(plan["current"]["mcp"], plan["target_mcp"]))
    lines.append(f"! auto-stash: {'yes' if plan['will_auto_stash'] else 'no'}")
    for warning in plan["warnings"]:
        lines.append(f"! warning: {warning}")
    lines.append("No files were changed.")
    return "\n".join(lines)


@click.command(
    help="Switch the active Claude work context or create one before switching.",
    short_help="Switch to a saved Claude context.",
)
@click.option(
    "-b",
    "create_name",
    default=None,
    help="Create a profile from the current state and switch to it",
)
@click.option(
    "--dry-run",
    is_flag=True,
    help="Preview profile, account, settings, and MCP changes without applying them.",
)
@click.argument("name", required=False)
def checkout(create_name: str | None, dry_run: bool, name: str | None) -> None:
    with cit_lock():
        state = read_state()
        current = state.get("activeProfile")
        if create_name:
            if dry_run:
                raise click.ClickException("--dry-run cannot be used with -b")
            save_current_profile(create_name, with_config=True)
            set_active_profile(create_name, current)
            click.echo(f"Switched to a new context stored as profile '{create_name}'")
            return
        if name is None:
            raise click.ClickException("A profile name is required")
        if name == "-":
            name = state.get("previousProfile")
            if name is None:
                raise click.ClickException("No previous profile")
        try:
            plan = _build_checkout_plan(current, name)
        except FileNotFoundError as error:
            raise click.ClickException(str(error)) from error
        if dry_run:
            click.echo(_render_checkout_plan(plan))
            return
        target = plan["target"]
        keychain.validate_keychain_access()
        for warning in plan["warnings"]:
            click.echo(f"Warning: {warning}")
        if plan["will_auto_stash"]:
            stash_id = create_stash_entry(
                message=f"auto: pre-checkout from {current or 'detached'}"
            )
            push_stash_id(stash_id)
        settings_overrides = plan["target_settings"]
        mcp_overrides = plan["target_mcp"]
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
            if settings_overrides:
                merge_settings(settings_overrides)
            update_wal_step(3)
            if mcp_overrides:
                merge_mcp(mcp_overrides)
            set_active_profile(name, current)
            clear_wal()
        except Exception as error:
            recover_if_needed()
            raise click.ClickException(str(error)) from error
        click.echo(f"Switched to context '{name}'")
