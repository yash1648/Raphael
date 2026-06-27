"""LLM Provider factory — creates providers from config."""

from app.llm.base import LLMProvider
from app.llm.nvidia_provider import NVIDIAProvider
from app.llm.openrouter_provider import OpenRouterProvider
from app.llm.ollama_provider import OllamaProvider


PROVIDER_MAP: dict[str, type[LLMProvider]] = {
    "nvidia": NVIDIAProvider,
    "openrouter": OpenRouterProvider,
    "ollama": OllamaProvider,
}


def create_llm(provider: str = "nvidia", **kwargs) -> LLMProvider:
    """Create an LLM provider by name.

    Args:
        provider: One of 'nvidia', 'openrouter', 'ollama'
        **kwargs: Passed to provider constructor (model, api_key, base_url, etc.)

    Returns:
        LLMProvider instance

    Raises:
        ValueError: If provider name is unknown
    """
    cls = PROVIDER_MAP.get(provider)
    if not cls:
        raise ValueError(f"Unknown LLM provider: {provider}. Available: {list(PROVIDER_MAP.keys())}")
    return cls(**kwargs)


def list_providers() -> list[str]:
    return list(PROVIDER_MAP.keys())
