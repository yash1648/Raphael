from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass
class LLMResponse:
    content: str
    model: str
    provider: str
    usage: dict[str, int] = field(default_factory=dict)
    raw: Any = None


class LLMProvider(ABC):
    """Abstract base for all LLM providers."""

    name: str = "base"
    model: str = ""

    def __init__(self, model: str | None = None, **kwargs):
        self.model = model or self.model
        self.extra_kwargs = kwargs

    @abstractmethod
    def generate(
        self,
        prompt: str,
        system_prompt: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        **kwargs,
    ) -> LLMResponse:
        ...

    @abstractmethod
    async def generate_async(
        self,
        prompt: str,
        system_prompt: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        **kwargs,
    ) -> LLMResponse:
        ...

    def count_tokens(self, text: str) -> int:
        """Rough token count estimate (4 chars per token)."""
        return len(text) // 4
