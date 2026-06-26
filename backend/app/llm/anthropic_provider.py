from anthropic import Anthropic, AsyncAnthropic

from app.llm.base import LLMProvider, LLMResponse


class AnthropicProvider(LLMProvider):
    name: str = "anthropic"
    model: str = "claude-sonnet-4-20250514"

    def __init__(self, model: str | None = None, api_key: str | None = None, **kwargs):
        super().__init__(model, **kwargs)
        self._client = Anthropic(api_key=api_key)
        self._async_client = AsyncAnthropic(api_key=api_key)

    def generate(
        self,
        prompt: str,
        system_prompt: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        **kwargs,
    ) -> LLMResponse:
        response = self._client.messages.create(
            model=self.model,
            system=system_prompt or "",
            messages=[{"role": "user", "content": prompt}],
            temperature=temperature,
            max_tokens=max_tokens,
            **{**self.extra_kwargs, **kwargs},
        )
        content = "".join(block.text for block in response.content if hasattr(block, "text"))
        return LLMResponse(
            content=content,
            model=self.model,
            provider=self.name,
            usage={
                "input_tokens": response.usage.input_tokens if response.usage else 0,
                "output_tokens": response.usage.output_tokens if response.usage else 0,
            },
            raw=response,
        )

    async def generate_async(
        self,
        prompt: str,
        system_prompt: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        **kwargs,
    ) -> LLMResponse:
        response = await self._async_client.messages.create(
            model=self.model,
            system=system_prompt or "",
            messages=[{"role": "user", "content": prompt}],
            temperature=temperature,
            max_tokens=max_tokens,
            **{**self.extra_kwargs, **kwargs},
        )
        content = "".join(block.text for block in response.content if hasattr(block, "text"))
        return LLMResponse(
            content=content,
            model=self.model,
            provider=self.name,
            usage={
                "input_tokens": response.usage.input_tokens if response.usage else 0,
                "output_tokens": response.usage.output_tokens if response.usage else 0,
            },
            raw=response,
        )
