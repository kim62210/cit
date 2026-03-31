from __future__ import annotations

from typing import Any

from cit.core.config_manager import checkout_overrides
from cit.core.profile import load_profile


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


def effective_profile_view(name: str) -> dict[str, Any]:
    target = load_profile(name)
    settings_overrides, mcp_overrides = checkout_overrides(name)
    target_settings = _build_target_settings(target, settings_overrides)
    target_mcp = _build_target_mcp(target, mcp_overrides)
    keychain_payload = target["keychain"].get("claudeAiOauth", {})
    oauth = target["oauth_account"]
    return {
        "name": name,
        "account": oauth.get("emailAddress", "unknown"),
        "subscription": keychain_payload.get("subscriptionType", "unknown"),
        "model": target_settings.get("model", "unknown"),
        "permission-mode": target_settings.get("permission-mode"),
        "mcp": target_mcp,
    }


def context_diff_payload(from_name: str, to_name: str) -> dict[str, Any]:
    source = effective_profile_view(from_name)
    target = effective_profile_view(to_name)
    changes: dict[str, Any] = {}
    if source["account"] != target["account"]:
        changes["account"] = {"from": source["account"], "to": target["account"]}
    if source["subscription"] != target["subscription"]:
        changes["subscription"] = {
            "from": source["subscription"],
            "to": target["subscription"],
        }
    if source["model"] != target["model"]:
        changes["model"] = {"from": source["model"], "to": target["model"]}
    source_permission = source.get("permission-mode") or "unset"
    target_permission = target.get("permission-mode") or "unset"
    if source_permission != target_permission:
        changes["permission_mode"] = {
            "from": source_permission,
            "to": target_permission,
        }
    mcp_changes = _describe_mcp_changes(source["mcp"], target["mcp"])
    if mcp_changes:
        changes["mcp"] = mcp_changes
    return {
        "from_profile": from_name,
        "to_profile": to_name,
        "source": source,
        "target": target,
        "changes": changes,
    }


def render_context_diff(from_name: str, to_name: str) -> str:
    payload = context_diff_payload(from_name, to_name)
    source = payload["source"]
    target = payload["target"]
    lines = [f"Diff: {from_name} -> {to_name}"]
    changes: list[str] = []
    if source["account"] != target["account"]:
        changes.append(f"Account: {source['account']} -> {target['account']}")
    if source["subscription"] != target["subscription"]:
        changes.append(
            f"~ subscription: {source['subscription']} -> {target['subscription']}"
        )
    if source["model"] != target["model"]:
        changes.append(f"~ model: {source['model']} -> {target['model']}")
    if source.get("permission-mode") != target.get("permission-mode"):
        source_permission = source.get("permission-mode") or "unset"
        target_permission = target.get("permission-mode") or "unset"
        changes.append(f"~ permission-mode: {source_permission} -> {target_permission}")
    changes.extend(_describe_mcp_changes(source["mcp"], target["mcp"]))
    if not changes:
        lines.append("No differences found.")
    else:
        lines.extend(changes)
    return "\n".join(lines)
