from __future__ import annotations

from datetime import datetime, timezone

import click

from cit.core import keychain
from cit.core.claude_files import read_oauth_account, read_settings
from cit.core.state import read_state


def _format_expiry(epoch_ms: int | None) -> str:
    if epoch_ms is None:
        return "unknown"
    expiry = datetime.fromtimestamp(epoch_ms / 1000, tz=timezone.utc)
    remaining = expiry - datetime.now(timezone.utc)
    if remaining.total_seconds() <= 0:
        return f"{expiry.isoformat()} (expired)"
    hours = int(remaining.total_seconds() // 3600)
    days, hours = divmod(hours, 24)
    return f"{expiry.strftime('%Y-%m-%d %H:%M:%S')} ({days}d {hours}h remaining)"


@click.command(
    help="Show the active profile, account details, model, and stash status.",
    short_help="Show the active account status.",
)
@click.option("--short", "short_output", is_flag=True, help="Show one-line summary")
def status(short_output: bool) -> None:
    state = read_state()
    keychain_payload = keychain.read_keychain_payload().get("claudeAiOauth", {})
    oauth = read_oauth_account()
    settings = read_settings()
    stash_count = len(state.get("stashStack", []))
    active_profile = state.get("activeProfile") or "detached"
    subscription = keychain_payload.get("subscriptionType") or "unknown"
    rate_limit = keychain_payload.get("rateLimitTier")
    email = oauth.get("emailAddress") or "unknown"
    model = settings.get("model") or "unknown"
    if short_output:
        click.echo(f"{active_profile} {email} {subscription} {model}")
        return
    click.echo(f"Profile:       {active_profile}")
    click.echo(f"Account:       {email}")
    click.echo(f"Display Name:  {oauth.get('displayName', 'unknown')}")
    click.echo(
        f"Organization:  {oauth.get('organizationName', 'unknown')} ({oauth.get('organizationRole', 'unknown')})"
    )
    click.echo(
        f"Subscription:  {subscription} (rateLimitTier: {rate_limit or 'unknown'})"
    )
    click.echo(f"Model:         {model}")
    click.echo(f"Token Expiry:  {_format_expiry(keychain_payload.get('expiresAt'))}")
    click.echo("")
    click.echo("Session:       unknown")
    click.echo(f"Stash:         {stash_count} entr{'y' if stash_count == 1 else 'ies'}")
