"""LLM client abstraction — Claude primary, GPT-4 fallback."""

import json
from anthropic import AsyncAnthropic
from openai import AsyncOpenAI

from backend.ai_engine.app.config import get_settings


class LLMClient:
    """Unified LLM interface with automatic fallback."""

    def __init__(self):
        settings = get_settings()
        self._anthropic = AsyncAnthropic(api_key=settings.anthropic_api_key) if settings.anthropic_api_key else None
        self._openai = AsyncOpenAI(api_key=settings.openai_api_key) if settings.openai_api_key else None
        self._primary_model = settings.llm_primary_model
        self._fallback_model = settings.llm_fallback_model

    async def generate(
        self,
        prompt: str,
        system: str = "",
        temperature: float = 0.7,
        max_tokens: int = 4096,
    ) -> str:
        """Generate text. Try Claude first, fall back to GPT-4."""
        # Try primary (Anthropic Claude)
        if self._anthropic:
            try:
                message = await self._anthropic.messages.create(
                    model=self._primary_model,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    system=system,
                    messages=[{"role": "user", "content": prompt}],
                )
                return message.content[0].text
            except Exception:
                pass  # Fall through to fallback

        # Fallback (OpenAI GPT-4)
        if self._openai:
            try:
                messages = []
                if system:
                    messages.append({"role": "system", "content": system})
                messages.append({"role": "user", "content": prompt})

                response = await self._openai.chat.completions.create(
                    model=self._fallback_model,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                )
                return response.choices[0].message.content or ""
            except Exception:
                pass

        # No LLM available — return empty
        raise RuntimeError("No LLM provider available. Set ANTHROPIC_API_KEY or OPENAI_API_KEY.")

    async def generate_json(
        self,
        prompt: str,
        system: str = "",
        temperature: float = 0.5,
        max_tokens: int = 4096,
    ) -> dict | list:
        """Generate and parse JSON output from LLM."""
        response = await self.generate(
            prompt=prompt,
            system=system + "\n\nOutput ONLY valid JSON. No markdown fences, no extra text.",
            temperature=temperature,
            max_tokens=max_tokens,
        )
        # Strip markdown fences if present
        text = response.strip()
        if text.startswith("```"):
            text = text.split("\n", 1)[1] if "\n" in text else text[3:]
        if text.endswith("```"):
            text = text[:-3]
        text = text.strip()

        return json.loads(text)


# Singleton
_client: LLMClient | None = None


def get_llm_client() -> LLMClient:
    global _client
    if _client is None:
        _client = LLMClient()
    return _client
