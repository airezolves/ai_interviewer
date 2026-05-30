"""
Model Factory for A2A Architecture.

Centralised model configuration for:
- LangChain LLMs (orchestrator synthesis, streaming)
- Instructor clients (intent analysis, planner, validator)

Supports dynamic per-request model selection via ContextVar:
1. If a ModelConfig is set via set_active_model(), use it.
2. Otherwise fall back to environment variables (existing behaviour).

Dynamic model config comes from mit.organization_setting rows, fetched
by model_id at request entry and set once for the whole request scope.

Provider mapping (DB provider → LiteLLM provider):
  google        → gemini       (use_litellm=true)
  google-vertex → vertex_ai    (use_litellm=true)
  openai        → openai       (use_litellm=true)
  anthropic     → anthropic    (use_litellm=true)
  azure         → azure        (use_litellm=true)
  deepseek      → deepseek     (use_litellm=true)
  openai-compatible → OpenAI SDK with custom endpoint (use_litellm=false)
  internal          → OpenAI SDK with custom endpoint (use_litellm=false)
"""

import base64
import logging
import os
from contextvars import ContextVar
from dataclasses import dataclass
from typing import Any, Dict, Optional, Tuple

logger = logging.getLogger(__name__)


# =============================================================================
# ModelConfig — unified representation of a resolved model
# =============================================================================

@dataclass(frozen=True)
class ModelConfig:
    """Resolved model configuration used by all LLM factories."""
    use_litellm: bool       # True → ChatLiteLLM / litellm completion; False → OpenAI SDK
    provider: str            # LiteLLM provider slug (gemini, openai, …) or empty
    model: str               # Model name (gemini-2.0-flash, gpt-4, etc.)
    api_key: str             # Decrypted API key
    endpoint: str            # Custom endpoint (openai-compatible / internal only)
    display_name: str        # Human-readable name for logs and DB storage


# DB provider → LiteLLM provider mapping
PROVIDER_MAP: Dict[str, str] = {
    "google": "gemini",
    "google-vertex": "vertex_ai",
    "openai": "openai",
    "anthropic": "anthropic",
    "azure": "azure",
    "deepseek": "deepseek",
}

# Providers that use the OpenAI-compatible (non-LiteLLM) path
LOCAL_PROVIDERS = {"openai-compatible", "internal", "ollama", "lmstudio"}


# =============================================================================
# Per-request ContextVar — set once at request entry, read by all factories
# =============================================================================

_active_model: ContextVar[Optional[ModelConfig]] = ContextVar(
    "active_model", default=None
)


def set_active_model(config: Optional[ModelConfig]):
    """Set the model config for the current request scope."""
    return _active_model.set(config)


def get_active_model() -> Optional[ModelConfig]:
    """Get the model config for the current request scope (or None)."""
    return _active_model.get(None)


# =============================================================================
# API key decryption (AES-256-GCM, compatible with Node.js EncryptionService)
# =============================================================================

_SALT_LEN = 64
_IV_LEN = 16
_TAG_LEN = 16
_KEY_LEN = 32
_ITERATIONS = 100_000


def decrypt_api_key(ciphertext_b64: str, master_key: str) -> str:
    """Decrypt an API key encrypted with AES-256-GCM + PBKDF2-HMAC-SHA512."""
    from cryptography.hazmat.backends import default_backend
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

    data = base64.b64decode(ciphertext_b64)
    salt = data[:_SALT_LEN]
    iv = data[_SALT_LEN : _SALT_LEN + _IV_LEN]
    tag = data[_SALT_LEN + _IV_LEN : _SALT_LEN + _IV_LEN + _TAG_LEN]
    ciphertext = data[_SALT_LEN + _IV_LEN + _TAG_LEN :]

    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA512(),
        length=_KEY_LEN,
        salt=salt,
        iterations=_ITERATIONS,
        backend=default_backend(),
    )
    key = kdf.derive(master_key.encode())
    decryptor = Cipher(
        algorithms.AES(key), modes.GCM(iv, tag), backend=default_backend()
    ).decryptor()
    return (decryptor.update(ciphertext) + decryptor.finalize()).decode("utf-8")


# =============================================================================
# Resolve DB config dict → ModelConfig
# =============================================================================

def resolve_db_model_config(db_config: Dict[str, Any]) -> ModelConfig:
    """
    Convert a raw organization_setting JSON dict into a ModelConfig.

    Handles provider mapping, API key decryption, and fallback logic.
    """
    db_provider = db_config.get("provider", "")
    model = db_config.get("model", "")
    endpoint = db_config.get("endpoint", "")
    encrypted_key = db_config.get("apiKeyEncrypted", "")

    # Decrypt API key if present
    api_key = ""
    if encrypted_key:
        master_key = os.getenv("AI_ENCRYPTION_MASTER_KEY", "")
        if master_key:
            try:
                api_key = decrypt_api_key(encrypted_key, master_key)
            except Exception as exc:
                logger.error("Failed to decrypt API key for model config: %s", exc)
        else:
            logger.warning("AI_ENCRYPTION_MASTER_KEY not set — cannot decrypt API key")

    # Determine litellm vs openai-compatible path
    if db_provider in LOCAL_PROVIDERS:
        return ModelConfig(
            use_litellm=False,
            provider="",
            model=model,
            api_key=api_key or os.getenv("LLAMA_API_KEY", ""),
            endpoint=endpoint or os.getenv("LLAMA_API_CHAT_ENDPOINT", "https://llm.manifestit.ai/v1"),
            display_name=model,
        )

    litellm_provider = PROVIDER_MAP.get(db_provider, db_provider)
    return ModelConfig(
        use_litellm=True,
        provider=litellm_provider,
        model=model,
        api_key=api_key,
        endpoint=endpoint,
        display_name=f"{litellm_provider}/{model}",
    )


# =============================================================================
# Internal resolver — ContextVar first, then env fallback
# =============================================================================

def _resolve_config() -> ModelConfig:
    """Return the active ModelConfig for this request (ContextVar → env fallback)."""
    config = _active_model.get(None)
    if config is not None:
        return config

    # Fallback to environment variables (original behaviour)
    use_litellm = os.getenv("AICHAT_USE_LLMLITE", "false").lower() == "true"
    if use_litellm:
        provider = os.getenv("LLMLITE_PROVIDER", "gemini")
        model = os.getenv("LLMLITE_MODEL", "gemini-2.0-flash")
        api_key = os.getenv("LLMLITE_API_KEY", "")
        return ModelConfig(
            use_litellm=True,
            provider=provider,
            model=model,
            api_key=api_key,
            endpoint="",
            display_name=f"{provider}/{model}",
        )
    else:
        endpoint = os.getenv("LLAMA_API_CHAT_ENDPOINT", "https://llm.manifestit.ai/v1")
        api_key = os.getenv("LLAMA_API_KEY", "")
        model = os.getenv("LLAMA_API_MODEL", "gemma3:12b")
        return ModelConfig(
            use_litellm=False,
            provider="",
            model=model,
            api_key=api_key,
            endpoint=endpoint,
            display_name=model,
        )


def get_model_display_name() -> str:
    """Return the display name for the current model (for DB storage)."""
    return _resolve_config().display_name


# =============================================================================
# LangChain LLM Factory (for orchestrator — synthesis, streaming)
# =============================================================================

def get_langchain_llm():
    """
    Get a LangChain Chat LLM based on current model config.

    Uses the active ModelConfig (ContextVar) if set, otherwise env vars.
    """
    cfg = _resolve_config()

    if cfg.use_litellm:
        from langchain_litellm import ChatLiteLLM

        full_model = (
            f"{cfg.provider}/{cfg.model}" if "/" not in cfg.model else cfg.model
        )
        logger.info("--- LangChain LLM: LiteLLM | %s ---", full_model)

        return ChatLiteLLM(
            model=full_model,
            temperature=0,
            api_key=cfg.api_key or None,
        )
    else:
        from langchain_openai import ChatOpenAI

        logger.info(
            "--- LangChain LLM: OpenAI-compat | %s | %s ---",
            cfg.endpoint, cfg.model,
        )
        return ChatOpenAI(
            base_url=cfg.endpoint,
            api_key=cfg.api_key or "not-needed",
            model=cfg.model,
            temperature=0,
        )


# =============================================================================
# Instructor Client Factory (for structured output)
# =============================================================================

def get_instructor_client(json_mode: bool = False):
    """
    Get an instructor-patched client based on current model config.

    Args:
        json_mode: If True, force instructor.Mode.JSON (used by planner).
                   If False, use default mode for LiteLLM or JSON for OpenAI-compat.

    Returns:
        tuple: (client, model_name_str, extra_kwargs_dict)
    """
    import instructor

    cfg = _resolve_config()

    if cfg.use_litellm:
        from litellm import completion

        full_model = (
            f"{cfg.provider}/{cfg.model}" if "/" not in cfg.model else cfg.model
        )
        logger.info("--- Instructor Client: LiteLLM | %s ---", full_model)

        mode = instructor.Mode.JSON if json_mode else None
        client = (
            instructor.from_litellm(completion, mode=mode)
            if mode
            else instructor.from_litellm(completion)
        )
        extra = {"api_key": cfg.api_key} if cfg.api_key else {}
        return client, full_model, extra
    else:
        from openai import OpenAI

        logger.info(
            "--- Instructor Client: OpenAI-compat | %s | %s ---",
            cfg.endpoint, cfg.model,
        )
        client = instructor.from_openai(
            OpenAI(base_url=cfg.endpoint, api_key=cfg.api_key or "not-needed"),
            mode=instructor.Mode.JSON,
        )
        return client, cfg.model, {}


# =============================================================================
# Async Streaming Completion (for token-by-token final answer streaming)
# =============================================================================

async def get_streaming_completion(
    messages: list,
    temperature: float = 0,
    max_tokens: int = 4096,
):
    """
    Async generator that yields token chunks from a streaming LLM completion.

    Uses the active ModelConfig (ContextVar) if set, otherwise env vars.
    Supports both LiteLLM and OpenAI-compatible providers.

    Yields:
        str: Individual token/chunk strings as they are generated.
    """
    cfg = _resolve_config()

    if cfg.use_litellm:
        import litellm

        full_model = (
            f"{cfg.provider}/{cfg.model}" if "/" not in cfg.model else cfg.model
        )
        logger.info("--- Streaming Completion: LiteLLM | %s ---", full_model)

        extra = {"api_key": cfg.api_key} if cfg.api_key else {}
        response = await litellm.acompletion(
            model=full_model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            stream=True,
            **extra,
        )
        async for chunk in response:
            choices = chunk.get("choices", []) if isinstance(chunk, dict) else getattr(chunk, "choices", [])
            if choices:
                delta = choices[0].get("delta", {}) if isinstance(choices[0], dict) else getattr(choices[0], "delta", None)
                if delta:
                    content = delta.get("content", "") if isinstance(delta, dict) else getattr(delta, "content", "")
                    if content:
                        yield content
    else:
        from openai import AsyncOpenAI

        logger.info(
            "--- Streaming Completion: OpenAI-compat | %s | %s ---",
            cfg.endpoint, cfg.model,
        )
        client = AsyncOpenAI(
            base_url=cfg.endpoint,
            api_key=cfg.api_key or "not-needed",
        )
        response = await client.chat.completions.create(
            model=cfg.model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            stream=True,
        )
        async for chunk in response:
            if chunk.choices and chunk.choices[0].delta and chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content
