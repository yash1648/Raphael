import os
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any
from contextlib import contextmanager
from threading import Lock


def resolve_api_key(env_var: str) -> str:
    """Resolve an API key from os.environ or from pydantic-settings.

    Tries os.environ first (set by main.py on uvicorn startup),
    then falls back to pydantic-settings (reads .env file).
    """
    key = os.environ.get(env_var, "")
    if key:
        return key
    try:
        from app.core.config import settings
        key = getattr(settings, env_var, "") or ""
    except Exception:
        pass
    return key


class ConnectionPool:
    """Connection pool for HTTP clients to improve performance and reduce resource usage."""
    
    _instance = None
    _lock = Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._clients = {}
                    cls._instance._client_locks = {}
        return cls._instance
    
    def get_client(self, provider_name: str, client_factory):
        """Get or create a client for the given provider."""
        with self._client_locks.setdefault(provider_name, Lock()):
            if provider_name not in self._clients:
                self._clients[provider_name] = client_factory()
            return self._clients[provider_name]
    
    def clear(self, provider_name: str = None):
        """Clear client(s) from pool."""
        if provider_name:
            self._clients.pop(provider_name, None)
            self._client_locks.pop(provider_name, None)
        else:
            self._clients.clear()
            self._client_locks.clear()


class TokenCache:
    """Simple token cache with TTL for LLM responses."""
    
    def __init__(self, ttl: int = 3600):
        self.cache = {}
        self.ttl = ttl
        self._lock = Lock()
    
    def get(self, key: str):
        """Get cached value if not expired."""
        with self._lock:
            if key in self.cache:
                timestamp, value = self.cache[key]
                if time.time() - timestamp < self.ttl:
                    return value
                del self.cache[key]
        return None
    
    def set(self, key: str, value):
        """Cache value with current timestamp."""
        with self._lock:
            self.cache[key] = (time.time(), value)
    
    def clear(self):
        """Clear all cached values."""
        with self._lock:
            self.cache.clear()


class ConversationWindow:
    """Manages conversation history with windowing to prevent memory leaks."""
    
    def __init__(self, max_history: int = 100):
        self.max_history = max_history
        self.history = []
        self._lock = Lock()
    
    def add(self, message: dict):
        """Add a message to conversation history."""
        with self._lock:
            self.history.append(message)
            # Trim history if it exceeds max size
            if len(self.history) > self.max_history:
                self.history = self.history[-self.max_history:]
    
    def get_all(self):
        """Get all conversation history."""
        with self._lock:
            return self.history.copy()
    
    def clear(self):
        """Clear conversation history."""
        with self._lock:
            self.history.clear()
    
    def __len__(self):
        with self._lock:
            return len(self.history)


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
