import httpx

from app.llm.base import LLMProvider, LLMResponse


class OllamaProvider(LLMProvider):
    """Local LLM via Ollama (self-hosted, free, private)."""

    name: str = "ollama"
    model: str = "llama3"
    base_url: str = "http://localhost:11434"

    def __init__(self, model: str | None = None, base_url: str | None = None, **kwargs):
        super().__init__(model, **kwargs)
        if base_url:
            self.base_url = base_url

    def _generate_sync(self, prompt: str, system_prompt: str | None = None, **kwargs) -> dict:
        payload = {
            "model": self.model,
            "prompt": prompt,
            "system": system_prompt or "",
            "stream": False,
            "options": {
                "temperature": kwargs.get("temperature", 0.7),
                "num_predict": kwargs.get("max_tokens", 4096),
            },
        }
        with httpx.Client(timeout=120) as client:
            resp = client.post(f"{self.base_url}/api/generate", json=payload)
            resp.raise_for_status()
            return resp.json()

    async def _generate_async(self, prompt: str, system_prompt: str | None = None, **kwargs) -> dict:
        payload = {
            "model": self.model,
            "prompt": prompt,
            "system": system_prompt or "",
            "stream": False,
            "options": {
                "temperature": kwargs.get("temperature", 0.7),
                "num_predict": kwargs.get("max_tokens", 4096),
            },
        }
        async with httpx.AsyncClient(timeout=120) as client:
            resp = await client.post(f"{self.base_url}/api/generate", json=payload)
            resp.raise_for_status()
            return resp.json()

    def generate(
        self,
        prompt: str,
        system_prompt: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        **kwargs,
    ) -> LLMResponse:
        data = self._generate_sync(prompt, system_prompt, temperature=temperature, max_tokens=max_tokens, **kwargs)
        return LLMResponse(
            content=data.get("response", ""),
            model=self.model,
            provider=self.name,
            usage={"eval_count": data.get("eval_count", 0)},
            raw=data,
        )

    async def generate_async(
        self,
        prompt: str,
        system_prompt: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        **kwargs,
    ) -> LLMResponse:
        data = await self._generate_async(prompt, system_prompt, temperature=temperature, max_tokens=max_tokens, **kwargs)
        return LLMResponse(
            content=data.get("response", ""),
            model=self.model,
            provider=self.name,
            usage={"eval_count": data.get("eval_count", 0)},
            raw=data,
        )
