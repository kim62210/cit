from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class ProfileConfig(BaseModel):
    model_config = ConfigDict(extra="allow")

    model: str | None = None
    permission_mode: str | None = Field(default=None, alias="permission-mode")
    auto_stash: bool | None = Field(default=None, alias="auto-stash")
    mcp: dict[str, Any] = Field(default_factory=dict)

    def to_toml_dict(self) -> dict[str, Any]:
        data = self.model_dump(exclude_none=True, by_alias=True)
        if not data.get("mcp"):
            data.pop("mcp", None)
        return data


class CitConfig(BaseModel):
    model_config = ConfigDict(extra="allow")

    global_config: ProfileConfig = Field(default_factory=ProfileConfig, alias="global")
    profiles: dict[str, ProfileConfig] = Field(default_factory=dict, alias="profile")

    def to_toml_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {"global": self.global_config.to_toml_dict()}
        if self.profiles:
            payload["profile"] = {
                name: config.to_toml_dict() for name, config in self.profiles.items()
            }
        return payload
