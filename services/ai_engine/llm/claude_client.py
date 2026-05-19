"""Claude (Anthropic) LLM client."""

import json

import anthropic

from shared.utils.logger import get_logger
from services.ai_engine.llm.base import BaseLLMClient
from services.ai_engine.config.settings import get_ai_engine_settings

logger = get_logger(__name__)
settings = get_ai_engine_settings()


class ClaudeClient(BaseLLMClient):
    """Anthropic Claude API client."""

    def __init__(self):
        self.client = anthropic.AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)
        self.model = settings.DEFAULT_MODEL

    async def generate(self, prompt: str, max_tokens: int = 4000, temperature: float = 0.7) -> str:
        """Generate a text response from Claude."""
        response = await self.client.messages.create(
            model=self.model,
            max_tokens=max_tokens,
            temperature=temperature,
            messages=[{"role": "user", "content": prompt}],
        )
        return response.content[0].text

    async def generate_json(self, prompt: str, max_tokens: int = 4000) -> dict:
        """Generate a JSON response from Claude."""
        full_prompt = f"{prompt}\n\nRespond with ONLY valid JSON. No markdown code fences, no explanation."

        response = await self.client.messages.create(
            model=self.model,
            max_tokens=max_tokens,
            temperature=0.3,  # Lower temperature for structured output
            messages=[{"role": "user", "content": full_prompt}],
        )

        content = response.content[0].text.strip()

        # Clean up markdown fences if present
        if content.startswith("```"):
            content = content.split("\n", 1)[1]
            content = content.rsplit("```", 1)[0].strip()

        try:
            return json.loads(content)
        except json.JSONDecodeError as e:
            logger.error("json_parse_failed", error=str(e), content_preview=content[:200])
            raise ValueError(f"LLM returned invalid JSON: {e}")
