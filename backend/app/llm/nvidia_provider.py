"""NVIDIA NIMs provider — uses NVIDIA's cloud API for LLM inference.

NVIDIA NIMs (NVIDIA Inference Microservices) provides OpenAI-compatible
chat completions at https://integrate.api.nvidia.com/v1.

Requires NVIDIA_API_KEY environment variable (nvapi-...).
Default model: meta/llama-3.1-70b-instruct
"""

import os
from openai import OpenAI, AsyncOpenAI

from app.llm.base import LLMProvider, LLMResponse

NVIDIA_BASE_URL = "https://integrate.api.nvidia.com/v1"


class NVIDIAProvider(LLMProvider):
    name: str = "nvidia"
    model: str = "meta/llama-3.1-70b-instruct"

    def __init__(self, model: str | None = None, api_key: str | None = None, **kwargs):
        super().__init__(model, **kwargs)
        resolved_key = api_key or os.environ.get("NVIDIA_API_KEY", "")
        safe_key = resolved_key if resolved_key else "no-key-configured"
        self._client = OpenAI(api_key=safe_key, base_url=NVIDIA_BASE_URL)
        self._async_client = AsyncOpenAI(api_key=safe_key, base_url=NVIDIA_BASE_URL)
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
