"""Base LLM client interface."""

from abc import ABC, abstractmethod


class BaseLLMClient(ABC):
    """Abstract base for LLM clients."""

    @abstractmethod
    async def generate(self, prompt: str, max_tokens: int = 4000, temperature: float = 0.7) -> str:
        """Generate a response from the LLM."""
        pass

    @abstractmethod
    async def generate_json(self, prompt: str, max_tokens: int = 4000) -> dict:
        """Generate a JSON response from the LLM."""
        pass
