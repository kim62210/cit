from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class ClaudeAiOauth(BaseModel):
    model_config = ConfigDict(extra="allow")

    accessToken: str | None = None
    refreshToken: str | None = None
    expiresAt: int | None = None
    scopes: list[str] = Field(default_factory=list)
    subscriptionType: str | None = None
    rateLimitTier: str | None = None


class KeychainPayload(BaseModel):
    model_config = ConfigDict(extra="allow")

    claudeAiOauth: ClaudeAiOauth


class OAuthAccount(BaseModel):
    model_config = ConfigDict(extra="allow")

    accountUuid: str | None = None
    emailAddress: str | None = None
    organizationUuid: str | None = None
    displayName: str | None = None
    organizationRole: str | None = None
    organizationName: str | None = None
    billingType: str | None = None
    subscriptionCreatedAt: str | None = None


class ProfileMeta(BaseModel):
    model_config = ConfigDict(extra="allow")

    name: str
    createdAt: int
    lastUsedAt: int | None = None
    sourceEmail: str | None = None
    sourceOrganization: str | None = None


class ProfileSnapshot(BaseModel):
    keychain: dict[str, Any]
    oauth_account: dict[str, Any]
    settings: dict[str, Any] | None = None
    mcp: dict[str, Any] | None = None
    meta: ProfileMeta
