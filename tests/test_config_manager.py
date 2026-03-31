from __future__ import annotations

import pytest

from cit.core.config_manager import (
    _coerce_value,
    get_config_value,
    read_config,
    set_config_value,
    unset_config_value,
)


def test_config_manager_supports_global_and_profile_values(env_paths):
    set_config_value("model", "sonnet", profile_name=None, global_scope=True)
    set_config_value("model", "opus[1m]", profile_name="work")

    config = read_config()

    assert config.global_config.model == "sonnet"
    assert config.profiles["work"].model == "opus[1m]"
    assert get_config_value("model", "work") == "opus[1m]"


def test_config_manager_unsets_nested_mcp_value(env_paths):
    set_config_value(
        "mcp.memory",
        '{"command": "npx", "args": ["@anthropic/memory-mcp"]}',
        profile_name="work",
    )

    unset_config_value("mcp.memory", "work")

    assert get_config_value("mcp.memory", "work") is None


def test_config_manager_rejects_unsupported_key(env_paths):
    with pytest.raises(ValueError, match="Unsupported key"):
        set_config_value("unsupported", "value", profile_name="work")


def test_coerce_value_handles_boolean_and_json_inputs():
    assert _coerce_value("auto-stash", "true") is True
    assert _coerce_value("auto-stash", "off") is False
    assert _coerce_value("mcp.memory", '{"command": "npx"}') == {"command": "npx"}
