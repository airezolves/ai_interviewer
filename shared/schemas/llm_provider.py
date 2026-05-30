"""Pydantic schemas for the per-user LLM provider system."""

from typing import Literal, Optional
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, Field

# Supported provider slugs (DB values).
ProviderSlug = Literal[
    "gemini",            # google → litellm 'gemini/'
    "openai",
    "anthropic",
    "deepseek",
    "azure",
    "openai-compatible", # generic OpenAI-compatible endpoint (LiteLLM is bypassed)
]


class LLMProviderCreate(BaseModel):
    provider: ProviderSlug
    model: str = Field(..., max_length=150, description="e.g. gemini-2.5-pro, gpt-4o, claude-sonnet-4-20250514")
    display_name: Optional[str] = Field(None, max_length=200)
    endpoint: Optional[str] = Field(None, max_length=500, description="Required for openai-compatible")
    api_key: str = Field(..., min_length=1, description="Plain key, encrypted server-side before storage")
    is_active: bool = False


class LLMProviderUpdate(BaseModel):
    model: Optional[str] = None
    display_name: Optional[str] = None
    endpoint: Optional[str] = None
    api_key: Optional[str] = None
    is_active: Optional[bool] = None


class LLMProviderRead(BaseModel):
    id: UUID
    provider: ProviderSlug
    model: str
    display_name: Optional[str] = None
    endpoint: Optional[str] = None
    api_key_masked: Optional[str] = None
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}
