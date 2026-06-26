"""Tests for LLM provider abstraction layer."""

from unittest.mock import MagicMock, patch

from app.llm.base import LLMProvider, LLMResponse
from app.llm.factory import create_llm, list_providers
from app.llm.ollama_provider import OllamaProvider


class MockProvider(LLMProvider):
    """Mock provider for testing."""
    name = "mock"
    model = "mock-model"

    def generate(self, prompt, system_prompt=None, temperature=0.7, max_tokens=4096, **kwargs):
        return LLMResponse(
            content=f"Mock response to: {prompt[:50]}",
            model=self.model,
            provider=self.name,
            usage={"total_tokens": 10},
        )

    async def generate_async(self, prompt, system_prompt=None, temperature=0.7, max_tokens=4096, **kwargs):
        return self.generate(prompt, system_prompt, temperature, max_tokens, **kwargs)


def test_list_providers():
    providers = list_providers()
    assert "nvidia" in providers
    assert "openrouter" in providers
    assert "openai" in providers
    assert "anthropic" in providers
    assert "ollama" in providers


def test_create_openai():
    provider = create_llm("openai", model="gpt-4o-mini")
    assert provider.name == "openai"
    assert provider.model == "gpt-4o-mini"


def test_create_anthropic():
    provider = create_llm("anthropic", model="claude-sonnet-4-20250514")
    assert provider.name == "anthropic"
    assert provider.model == "claude-sonnet-4-20250514"


def test_create_ollama():
    provider = create_llm("ollama", model="llama3", base_url="http://localhost:11434")
    assert provider.name == "ollama"
    assert provider.model == "llama3"


def test_create_nvidia():
    provider = create_llm("nvidia", model="meta/llama-3.1-8b-instruct")
    assert provider.name == "nvidia"
    assert provider.model == "meta/llama-3.1-8b-instruct"
    assert provider._has_credentials is False


def test_create_openrouter():
    provider = create_llm("openrouter", model="mistralai/mixtral-8x22b-instruct")
    assert provider.name == "openrouter"
    assert provider.model == "mistralai/mixtral-8x22b-instruct"
    assert provider._has_credentials is False


def test_create_unknown_provider():
    try:
        create_llm("nonexistent")
        assert False, "Should have raised ValueError"
    except ValueError:
        pass


def test_mock_provider_generate():
    provider = MockProvider()
    response = provider.generate("Hello world", system_prompt="Be helpful")
    assert response.content.startswith("Mock response to:")
    assert response.provider == "mock"
    assert response.model == "mock-model"
    assert response.usage["total_tokens"] == 10


def test_llm_response_dataclass():
    response = LLMResponse(
        content="Test response",
        model="gpt-4",
        provider="openai",
        usage={"total_tokens": 100},
    )
    assert response.content == "Test response"
    assert response.model == "gpt-4"
    assert response.provider == "openai"
    assert response.usage["total_tokens"] == 100


def test_count_tokens():
    provider = MockProvider()
    text = "Hello world, this is a test of token counting!"
    count = provider.count_tokens(text)
    assert count == len(text) // 4
    assert count > 0


@patch("httpx.Client")
def test_ollama_provider(mock_client):
    """Test Ollama provider with mocked HTTP."""
    mock_response = MagicMock()
    mock_response.json.return_value = {"response": "Ollama response"}
    mock_client.return_value.__enter__.return_value.post.return_value = mock_response

    provider = OllamaProvider(model="llama3", base_url="http://localhost:11434")
    # Override _generate_sync to use mock
    provider._generate_sync = lambda prompt, system_prompt=None, **kwargs: {"response": "Mocked Ollama response"}
    response = provider.generate("Hello")
    assert response.content == "Mocked Ollama response"
    assert response.provider == "ollama"


def test_create_llm_preserves_kwargs():
    provider = create_llm("openai", model="gpt-4o-mini", api_key="test-key")
    assert provider.model == "gpt-4o-mini"


def test_nvidia_provider_create_with_key():
    provider = create_llm("nvidia", api_key="nv-test-key", model="test-model")
    assert provider.name == "nvidia"
    assert provider.model == "test-model"
    assert provider._has_credentials is True


def test_openrouter_provider_create_with_key():
    provider = create_llm("openrouter", api_key="or-test-key", model="test-model")
    assert provider.name == "openrouter"
    assert provider.model == "test-model"
    assert provider._has_credentials is True


def test_default_provider_is_nvidia():
    provider = create_llm()
    assert provider.name == "nvidia"
    assert provider.model == "meta/llama-3.1-405b-instruct"
