"""OpenAI LLM client (fallback)."""

import json

import openai

from shared.utils.logger import get_logger
from services.ai_engine.llm.base import BaseLLMClient
from services.ai_engine.config.settings import get_ai_engine_settings

logger = get_logger(__name__)
settings = get_ai_engine_settings()


class OpenAIClient(BaseLLMClient):
    """OpenAI API client (fallback provider)."""

    def __init__(self):
        self.client = openai.AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        self.model = "gpt-4o"

    async def generate(self, prompt: str, max_tokens: int = 4000, temperature: float = 0.7) -> str:
        """Generate a text response from OpenAI."""
        response = await self.client.chat.completions.create(
            model=self.model,
            max_tokens=max_tokens,
            temperature=temperature,
            messages=[{"role": "user", "content": prompt}],
        )
        return response.choices[0].message.content or ""

    async def generate_json(self, prompt: str, max_tokens: int = 4000) -> dict:
        """Generate a JSON response from OpenAI."""
        full_prompt = f"{prompt}\n\nRespond with ONLY valid JSON. No markdown code fences, no explanation."

        response = await self.client.chat.completions.create(
            model=self.model,
            max_tokens=max_tokens,
            temperature=0.3,
            response_format={"type": "json_object"},
            messages=[{"role": "user", "content": full_prompt}],
        )

        content = response.choices[0].message.content or "{}"
        try:
            return json.loads(content)
        except json.JSONDecodeError as e:
            logger.error("openai_json_parse_failed", error=str(e))
            raise ValueError(f"OpenAI returned invalid JSON: {e}")
