"""
Model Factory — per-user LLM resolution.

Mirrors the reference `model_factory.py` but the active ModelConfig is loaded
from the `user_llm_providers` table (per-user) rather than an org table.

Resolution order for a request:
  1. Active ModelConfig set via `set_active_model()` (ContextVar) — typically
     populated by middleware or service-level helpers from the DB.
  2. Server-default env vars (LLM_PROVIDER, LLM_MODEL, GEMINI_API_KEY, etc.).
"""

from __future__ import annotations

import logging
import os
from contextvars import ContextVar
from dataclasses import dataclass
from typing import Any, Dict, Optional

from shared.security import decrypt_secret

logger = logging.getLogger(__name__)


# DB provider → LiteLLM provider slug
PROVIDER_MAP: Dict[str, str] = {
    "gemini": "gemini",
    "google": "gemini",
    "google-vertex": "vertex_ai",
    "openai": "openai",
    "anthropic": "anthropic",
    "azure": "azure",
    "deepseek": "deepseek",
}

LOCAL_PROVIDERS = {"openai-compatible", "internal", "ollama", "lmstudio"}


@dataclass(frozen=True)
class ModelConfig:
    """Resolved model configuration used by all LLM factories."""
    use_litellm: bool       # True → ChatLiteLLM / litellm; False → OpenAI SDK against custom endpoint
    provider: str           # LiteLLM provider slug or empty
    model: str
    api_key: str
    endpoint: str
    display_name: str


_active_model: ContextVar[Optional[ModelConfig]] = ContextVar("active_model", default=None)


def set_active_model(config: Optional[ModelConfig]):
    return _active_model.set(config)


def reset_active_model(token):
    _active_model.reset(token)


def get_active_model() -> Optional[ModelConfig]:
    return _active_model.get(None)


# ─────────────────────────────────────────────────────────────────
#  Building ModelConfig from a DB row
# ─────────────────────────────────────────────────────────────────

def model_config_from_db_row(row: Dict[str, Any]) -> ModelConfig:
    """
    Build a ModelConfig from a `user_llm_providers` DB row dict.

    Expected keys: provider, model, endpoint, api_key_encrypted, display_name.
    The encrypted key is decrypted using AI_ENCRYPTION_MASTER_KEY from env.
    """
    db_provider = (row.get("provider") or "").lower()
    model = row.get("model") or ""
    endpoint = row.get("endpoint") or ""
    encrypted_key = row.get("api_key_encrypted") or ""
    display_name = row.get("display_name") or model

    api_key = ""
    if encrypted_key:
        master_key = os.getenv("AI_ENCRYPTION_MASTER_KEY", "")
        if not master_key:
            logger.warning("AI_ENCRYPTION_MASTER_KEY not set — cannot decrypt user API key")
        else:
            try:
                api_key = decrypt_secret(encrypted_key, master_key)
            except Exception as exc:
                logger.error("Failed to decrypt user API key: %s", exc)

    if db_provider in LOCAL_PROVIDERS:
        return ModelConfig(
            use_litellm=False,
            provider="",
            model=model,
            api_key=api_key,
            endpoint=endpoint,
            display_name=display_name,
        )

    litellm_provider = PROVIDER_MAP.get(db_provider, db_provider)
    return ModelConfig(
        use_litellm=True,
        provider=litellm_provider,
        model=model,
        api_key=api_key,
        endpoint=endpoint,
        display_name=display_name,
    )


# ─────────────────────────────────────────────────────────────────
#  Server-default fallback (when no per-user provider exists)
# ─────────────────────────────────────────────────────────────────

def _env_default_config() -> ModelConfig:
    provider = os.getenv("LLM_PROVIDER", "gemini").lower()
    model = os.getenv("LLM_MODEL", "gemini-2.5-pro")

    if provider == "openai-compatible":
        endpoint = os.getenv("LLM_ENDPOINT", "")
        api_key = os.getenv("LLM_API_KEY", "")
        return ModelConfig(
            use_litellm=False, provider="", model=model,
            api_key=api_key, endpoint=endpoint, display_name=model,
        )

    api_key = ""
    if provider in ("gemini", "google"):
        api_key = os.getenv("GEMINI_API_KEY", "")
    elif provider == "openai":
        api_key = os.getenv("OPENAI_API_KEY", "")
    elif provider == "anthropic":
        api_key = os.getenv("ANTHROPIC_API_KEY", "")
    else:
        api_key = os.getenv(f"{provider.upper()}_API_KEY", "")

    litellm_provider = PROVIDER_MAP.get(provider, provider)
    return ModelConfig(
        use_litellm=True, provider=litellm_provider, model=model,
        api_key=api_key, endpoint="",
        display_name=f"{litellm_provider}/{model}",
    )


def _resolve_config() -> ModelConfig:
    cfg = _active_model.get(None)
    return cfg if cfg is not None else _env_default_config()


def get_model_display_name() -> str:
    return _resolve_config().display_name


# ─────────────────────────────────────────────────────────────────
#  Factories
# ─────────────────────────────────────────────────────────────────

def get_langchain_llm(temperature: float = 0):
    """Return a LangChain Chat LLM bound to the active ModelConfig."""
    cfg = _resolve_config()
    if cfg.use_litellm:
        from langchain_litellm import ChatLiteLLM
        full_model = f"{cfg.provider}/{cfg.model}" if "/" not in cfg.model else cfg.model
        logger.info("LangChain LLM: LiteLLM | %s", full_model)
        return ChatLiteLLM(model=full_model, temperature=temperature, api_key=cfg.api_key or None)

    from langchain_openai import ChatOpenAI
    logger.info("LangChain LLM: OpenAI-compat | %s | %s", cfg.endpoint, cfg.model)
    return ChatOpenAI(
        base_url=cfg.endpoint or None,
        api_key=cfg.api_key or "not-needed",
        model=cfg.model,
        temperature=temperature,
    )


def get_instructor_client(json_mode: bool = False):
    """Return (instructor_client, model_name, extra_kwargs) for structured output."""
    import instructor

    cfg = _resolve_config()

    if cfg.use_litellm:
        from litellm import completion
        full_model = f"{cfg.provider}/{cfg.model}" if "/" not in cfg.model else cfg.model
        logger.info("Instructor: LiteLLM | %s", full_model)
        mode = instructor.Mode.JSON if json_mode else None
        client = instructor.from_litellm(completion, mode=mode) if mode else instructor.from_litellm(completion)
        extra = {"api_key": cfg.api_key} if cfg.api_key else {}
        return client, full_model, extra

    from openai import OpenAI
    logger.info("Instructor: OpenAI-compat | %s | %s", cfg.endpoint, cfg.model)
    client = instructor.from_openai(
        OpenAI(base_url=cfg.endpoint or None, api_key=cfg.api_key or "not-needed"),
        mode=instructor.Mode.JSON,
    )
    return client, cfg.model, {}


def get_async_instructor_client(json_mode: bool = False):
    """Async variant — returns (client, model, extra) with async completion bound."""
    import instructor

    cfg = _resolve_config()

    if cfg.use_litellm:
        from litellm import acompletion
        full_model = f"{cfg.provider}/{cfg.model}" if "/" not in cfg.model else cfg.model
        mode = instructor.Mode.JSON if json_mode else None
        client = instructor.from_litellm(acompletion, mode=mode) if mode else instructor.from_litellm(acompletion)
        extra = {"api_key": cfg.api_key} if cfg.api_key else {}
        return client, full_model, extra

    from openai import AsyncOpenAI
    client = instructor.from_openai(
        AsyncOpenAI(base_url=cfg.endpoint or None, api_key=cfg.api_key or "not-needed"),
        mode=instructor.Mode.JSON,
    )
    return client, cfg.model, {}
