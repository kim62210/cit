from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import click

from cit.core import config_manager, keychain, profile, state, wal
from cit.core.lock import cit_lock, is_lock_held
from cit.core.paths import get_cit_home, get_claude_home


@dataclass
class DiagnosticResult:
    name: str
    status: str
    detail: str | None = None


def _check_wal() -> DiagnosticResult:
    wal_path_obj = wal.wal_path()
    if not wal_path_obj.exists():
        return DiagnosticResult(
            name="WAL",
            status="ok",
            detail=f"No WAL file (no pending recovery)",
        )
    payload = wal.read_wal()
    if payload is None:
        return DiagnosticResult(
            name="WAL",
            status="error",
            detail="WAL file is corrupted - recovery may be needed on next run",
        )
    backup = payload.get("backup", {})
    steps = payload.get("steps", [])
    return DiagnosticResult(
        name="WAL",
        status="warning",
        detail=f"Pending WAL entry: {len(steps)} step(s), backup keys: {list(backup.keys())}",
    )


def _check_keychain() -> DiagnosticResult:
    try:
        keychain.validate_keychain_access()
        payload = keychain.read_keychain_payload()
        has_oauth = "claudeAiOauth" in payload
        return DiagnosticResult(
            name="Keychain",
            status="ok" if has_oauth else "warning",
            detail=f"Access OK, has oauth data: {has_oauth}",
        )
    except RuntimeError as e:
        return DiagnosticResult(
            name="Keychain",
            status="error",
            detail=str(e),
        )


def _check_config() -> DiagnosticResult:
    config_path_obj = config_manager.config_path()
    if not config_path_obj.exists():
        return DiagnosticResult(
            name="Config",
            status="ok",
            detail="No config.toml (using defaults)",
        )
    try:
        config = config_manager.read_config()
        profile_count = len(config.profiles)
        return DiagnosticResult(
            name="Config",
            status="ok",
            detail=f"Valid TOML, {profile_count} profile(s) with custom config",
        )
    except Exception as e:
        return DiagnosticResult(
            name="Config",
            status="error",
            detail=f"Invalid TOML: {e}",
        )


def _check_profiles() -> DiagnosticResult:
    profiles_dir_obj = profile.profiles_dir()
    if not profiles_dir_obj.exists():
        return DiagnosticResult(
            name="Profiles",
            status="warning",
            detail="Profiles directory does not exist",
        )
    profiles = profile.list_profiles()
    if not profiles:
        return DiagnosticResult(
            name="Profiles",
            status="ok",
            detail="No saved profiles",
        )
    corrupted = []
    for name in profiles:
        try:
            profile.load_profile(name)
        except Exception as e:
            corrupted.append(f"{name} ({e})")
    if corrupted:
        return DiagnosticResult(
            name="Profiles",
            status="error",
            detail=f"Corrupted profiles: {', '.join(corrupted)}",
        )
    return DiagnosticResult(
        name="Profiles",
        status="ok",
        detail=f"{len(profiles)} profile(s): {', '.join(profiles)}",
    )


def _check_state() -> DiagnosticResult:
    state_path_obj = state.state_path()
    if not state_path_obj.exists():
        return DiagnosticResult(
            name="State",
            status="ok",
            detail="No state.json (will use defaults)",
        )
    try:
        state_data = state.read_state()
        active = state_data.get("activeProfile") or "detached"
        previous = state_data.get("previousProfile") or "none"
        stash_count = len(state_data.get("stashStack", []))
        return DiagnosticResult(
            name="State",
            status="ok",
            detail=f"active={active}, previous={previous}, stash={stash_count}",
        )
    except Exception as e:
        return DiagnosticResult(
            name="State",
            status="error",
            detail=f"Invalid JSON: {e}",
        )


def _check_lock() -> DiagnosticResult:
    cit_dir = get_cit_home()
    lock_path = cit_dir / ".lock"
    if not lock_path.exists():
        return DiagnosticResult(
            name="Lock",
            status="ok",
            detail="No lock file (no active session)",
        )
    held = is_lock_held()
    if held:
        return DiagnosticResult(
            name="Lock",
            status="warning",
            detail=f"Lock is currently held by another cit process",
        )
    return DiagnosticResult(
        name="Lock",
        status="ok",
        detail="Lock file exists but is not held",
    )


def _check_paths() -> DiagnosticResult:
    issues: list[str] = []
    cit_home = get_cit_home()
    claude_home = get_claude_home()
    if not cit_home.exists():
        issues.append("CIT_HOME does not exist")
    if not claude_home.exists():
        issues.append("CLAUDE_HOME does not exist")
    if issues:
        return DiagnosticResult(
            name="Paths",
            status="error",
            detail=", ".join(issues),
        )
    return DiagnosticResult(
        name="Paths",
        status="ok",
        detail=f"CIT_HOME={cit_home}, CLAUDE_HOME={claude_home}",
    )


def run_all_checks() -> list[DiagnosticResult]:
    checks = [
        _check_wal,
        _check_keychain,
        _check_config,
        _check_profiles,
        _check_state,
        _check_lock,
        _check_paths,
    ]
    return [check() for check in checks]


def has_errors(results: list[DiagnosticResult]) -> bool:
    return any(r.status == "error" for r in results)


def has_warnings(results: list[DiagnosticResult]) -> bool:
    return any(r.status == "warning" for r in results)


@click.command(
    help="Run diagnostics on cit state: WAL, Keychain, config, profiles, state, and paths.",
    short_help="Run cit health diagnostics.",
)
@click.option(
    "--json", "json_output", is_flag=True, help="Show machine-readable JSON output"
)
def doctor(json_output: bool) -> None:
    results = run_all_checks()
    if json_output:
        output: dict[str, Any] = {
            "ok": not has_errors(results),
            "errors": [r.name for r in results if r.status == "error"],
            "warnings": [r.name for r in results if r.status == "warning"],
            "checks": {
                r.name: {"status": r.status, "detail": r.detail} for r in results
            },
        }
        click.echo(json.dumps(output, indent=2))
        return
    click.echo("Running cit diagnostics...\n")
    error_count = 0
    warning_count = 0
    for result in results:
        icon = {"ok": "✓", "warning": "!", "error": "✗"}[result.status]
        color = {"ok": "green", "warning": "yellow", "error": "red"}[result.status]
        prefix = click.style(f"[{icon}]", fg=color)
        click.echo(f"{prefix} {result.name}: {result.detail or 'OK'}")
        if result.status == "error":
            error_count += 1
        elif result.status == "warning":
            warning_count += 1
    click.echo("")
    if error_count > 0:
        click.echo(
            click.style(
                f"Found {error_count} error(s). Run 'cit status' for more details.",
                fg="red",
            )
        )
    elif warning_count > 0:
        click.echo(
            click.style(
                f"Found {warning_count} warning(s). No critical issues found.",
                fg="yellow",
            )
        )
    else:
        click.echo(click.style("All checks passed.", fg="green"))
