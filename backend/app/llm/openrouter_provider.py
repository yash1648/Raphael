"""OpenRouter provider — routes LLM requests to multiple model providers.

OpenRouter (https://openrouter.ai) provides a unified API that routes
to 200+ models across OpenAI, Anthropic, Google, Meta, Mistral, and more.

Uses OpenAI-compatible chat completions at https://openrouter.ai/api/v1.

Requires OPENROUTER_API_KEY environment variable.
"""

import os
from openai import OpenAI, AsyncOpenAI

from app.llm.base import LLMProvider, LLMResponse, resolve_api_key, ConnectionPool

OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"

# Global connection pool instance
_connection_pool = ConnectionPool()


class OpenRouterProvider(LLMProvider):
    name: str = "openrouter"
    model: str = "openrouter/free"  # Free models router — auto-selects from 25+ free models

    def __init__(self, model: str | None = None, api_key: str | None = None, **kwargs):
        super().__init__(model, **kwargs)
        resolved_key = api_key or resolve_api_key("OPENROUTER_API_KEY")
        safe_key = resolved_key if resolved_key else "no-key-configured"

        # OpenRouter recommends identifying your app via headers
        default_headers = {
            "HTTP-Referer": "https://github.com/yash1648/Raphael",
            "X-Title": "Raphael AI Assistant",
        }
        self._client = OpenAI(
            api_key=safe_key,
            base_url=OPENROUTER_BASE_URL,
            default_headers=default_headers,
        )
        self._async_client = AsyncOpenAI(
            api_key=safe_key,
            base_url=OPENROUTER_BASE_URL,
            default_headers=default_headers,
        )
        self._has_credentials = bool(resolved_key)

    def generate(
        self,
        prompt: str,
        system_prompt: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        **kwargs,
    ) -> LLMResponse:
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        response = self._client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            **{**self.extra_kwargs, **kwargs},
        )
        choice = response.choices[0]
        return LLMResponse(
            content=choice.message.content or "",
            model=self.model,
            provider=self.name,
            usage={
                "prompt_tokens": response.usage.prompt_tokens if response.usage else 0,
                "completion_tokens": response.usage.completion_tokens if response.usage else 0,
                "total_tokens": response.usage.total_tokens if response.usage else 0,
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
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        response = await self._async_client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            **{**self.extra_kwargs, **kwargs},
        )
        choice = response.choices[0]
        return LLMResponse(
            content=choice.message.content or "",
            model=self.model,
            provider=self.name,
            usage={
                "prompt_tokens": response.usage.prompt_tokens if response.usage else 0,
                "completion_tokens": response.usage.completion_tokens if response.usage else 0,
                "total_tokens": response.usage.total_tokens if response.usage else 0,
            },
            raw=response,
        )
