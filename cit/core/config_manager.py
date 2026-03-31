from __future__ import annotations

import json
import tomllib
from pathlib import Path
from typing import Any

import tomli_w

from cit.core.state import ensure_cit_dirs
from cit.models.config import CitConfig, ProfileConfig


SUPPORTED_KEYS = {"model", "permission-mode", "auto-stash"}


def config_path() -> Path:
    return ensure_cit_dirs() / "config.toml"


def read_config() -> CitConfig:
    path = config_path()
    if not path.exists():
        return CitConfig.model_validate({})
    with path.open("rb") as file:
        raw = tomllib.load(file)
    return CitConfig.model_validate(raw)


def write_config(config: CitConfig) -> None:
    path = config_path()
    with path.open("wb") as file:
        tomli_w.dump(config.to_toml_dict(), file)


def _get_profile_config(config: CitConfig, profile_name: str) -> ProfileConfig:
    profile = config.profiles.get(profile_name)
    if profile is None:
        profile = ProfileConfig()
        config.profiles[profile_name] = profile
    return profile


def _assign_value(target: dict[str, Any], key: str, value: Any) -> None:
    if key.startswith("mcp."):
        _, server = key.split(".", 1)
        target.setdefault("mcp", {})[server] = (
            value if isinstance(value, dict) else json.loads(value)
        )
        return
    if key not in SUPPORTED_KEYS:
        raise ValueError(f"Unsupported key: {key}")
    target[key] = value


def set_config_value(
    key: str, value: str, profile_name: str | None, global_scope: bool = False
) -> None:
    config = read_config()
    if global_scope:
        payload = config.global_config.to_toml_dict()
        _assign_value(payload, key, _coerce_value(key, value))
        config.global_config = ProfileConfig.model_validate(payload)
    else:
        if not profile_name:
            raise ValueError("An active profile is required for profile-scoped config")
        current = _get_profile_config(config, profile_name).to_toml_dict()
        _assign_value(current, key, _coerce_value(key, value))
        config.profiles[profile_name] = ProfileConfig.model_validate(current)
    write_config(config)


def get_config_value(key: str, profile_name: str | None) -> Any:
    resolved = resolve_config(profile_name)
    if key.startswith("mcp."):
        _, server = key.split(".", 1)
        return resolved.get("mcp", {}).get(server)
    return resolved.get(key)


def unset_config_value(key: str, profile_name: str) -> None:
    config = read_config()
    profile = _get_profile_config(config, profile_name).to_toml_dict()
    if key.startswith("mcp."):
        _, server = key.split(".", 1)
        profile.get("mcp", {}).pop(server, None)
    else:
        profile.pop(key, None)
    config.profiles[profile_name] = ProfileConfig.model_validate(profile)
    write_config(config)


def resolve_config(profile_name: str | None) -> dict[str, Any]:
    config = read_config()
    resolved = {"auto-stash": True}
    resolved.update(config.global_config.to_toml_dict())
    if profile_name and profile_name in config.profiles:
        resolved.update(config.profiles[profile_name].to_toml_dict())
    return resolved


def list_profile_config(profile_name: str | None) -> dict[str, Any]:
    return resolve_config(profile_name)


def _coerce_value(key: str, value: str) -> Any:
    if key == "auto-stash":
        return value.lower() in {"1", "true", "yes", "on"}
    if key.startswith("mcp."):
        return json.loads(value)
    return value
