from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class TokenUsage(BaseModel):
    model_config = ConfigDict(extra="ignore")

    input_tokens: int = 0
    output_tokens: int = 0
    cache_creation_input_tokens: int = 0
    cache_read_input_tokens: int = 0


class SessionEntry(BaseModel):
    model_config = ConfigDict(extra="allow")

    session_id: str
    project_slug: str
    model: str | None = None
    started_at: str | None = None
    usage: TokenUsage = Field(default_factory=TokenUsage)
