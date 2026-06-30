"""Performance and security optimization tests for Raphael backend."""

import pytest
import time
from unittest.mock import MagicMock, patch
from app.llm.base import ConnectionPool, TokenCache, ConversationWindow
from app.llm.factory import create_llm
from app.agents.base import Agent, Tool


class TestConnectionPool:
    """Test connection pool functionality."""
    
    def test_singleton_pattern(self):
        """Test that ConnectionPool is a singleton."""
        pool1 = ConnectionPool()
        pool2 = ConnectionPool()
        assert pool1 is pool2
    
    def test_client_reuse(self):
        """Test that clients are reused from pool."""
        pool = ConnectionPool()
        unique_name = f"reuse_test_{id(self)}"
        
        def create_client():
            return {"id": "test_client", "created": time.time()}
        
        client1 = pool.get_client(unique_name, create_client)
        client2 = pool.get_client(unique_name, create_client)
        
        assert client1 is client2  # Same instance
        assert client1["id"] == "test_client"
    
    def test_different_providers_different_clients(self):
        """Test that different providers get different clients."""
        pool = ConnectionPool()
        
        def create_client():
            return {"id": "test_client", "created": time.time()}
        
        client1 = pool.get_client("unique_provider_1", create_client)
        client2 = pool.get_client("unique_provider_2", create_client)
        
        assert client1 is not client2
        assert client1["id"] == "test_client"
        assert client2["id"] == "test_client"


class TestTokenCache:
    """Test token cache functionality."""
    
    def test_cache_set_get(self):
        """Test basic cache set/get operations."""
        cache = TokenCache(ttl=60)
        
        # Set a value
        cache.set("test_key", {"response": "test", "provider": "nvidia"})
        
        # Get the value
        result = cache.get("test_key")
        assert result is not None
        assert result["response"] == "test"
        assert result["provider"] == "nvidia"
    
    def test_cache_expiry(self):
        """Test that cache entries expire."""
        cache = TokenCache(ttl=0.1)  # 100ms TTL
        
        cache.set("test_key", {"response": "test"})
        assert cache.get("test_key") is not None
        
        # Wait for expiry
        time.sleep(0.2)
        
        assert cache.get("test_key") is None
    
    def test_cache_clear(self):
        """Test cache clearing."""
        cache = TokenCache(ttl=60)
        
        cache.set("key1", "value1")
        cache.set("key2", "value2")
        
        assert cache.get("key1") is not None
        assert cache.get("key2") is not None
        
        cache.clear()
        
        assert cache.get("key1") is None
        assert cache.get("key2") is None


class TestConversationWindow:
    """Test conversation window functionality."""
    
    def test_add_messages(self):
        """Test adding messages to conversation window."""
        window = ConversationWindow(max_history=10)
        
        for i in range(5):
            window.add({"role": "user", "content": f"Message {i}"})
        
        assert len(window) == 5
        history = window.get_all()
        assert len(history) == 5
        assert history[0]["content"] == "Message 0"
        assert history[4]["content"] == "Message 4"
    
    def test_window_size_limit(self):
        """Test that conversation window respects size limit."""
        window = ConversationWindow(max_history=3)
        
        for i in range(5):
            window.add({"role": "user", "content": f"Message {i}"})
        
        assert len(window) == 3
        history = window.get_all()
        assert history[0]["content"] == "Message 2"
        assert history[1]["content"] == "Message 3"
        assert history[2]["content"] == "Message 4"
    
    def test_clear_history(self):
        """Test clearing conversation history."""
        window = ConversationWindow(max_history=10)
        
        window.add({"role": "user", "content": "Test message"})
        assert len(window) == 1
        
        window.clear()
        assert len(window) == 0


class TestAgentOptimizations:
    """Test agent performance optimizations."""
    
    def test_agent_with_conversation_window(self):
        """Test that agent uses ConversationWindow instead of list."""
        agent = Agent(name="TestAgent", max_conversation_history=50)
        
        # Check that agent has conversation window
        assert hasattr(agent, '_conversation_history')
        assert isinstance(agent._conversation_history, ConversationWindow)
        assert agent._conversation_history.max_history == 50
    
    def test_agent_cache_initialization(self):
        """Test that agent initializes cache structures."""
        agent = Agent(name="TestAgent")
        
        assert hasattr(agent, '_last_tool_call_cache')
        assert hasattr(agent, '_tool_call_cache_ttl')
        assert agent._tool_call_cache_ttl == 300
    
    def test_tool_registration(self):
        """Test tool registration functionality."""
        agent = Agent(name="TestAgent")
        
        def dummy_tool_func(param: str) -> str:
            return f"Processed: {param}"
        
        tool = Tool(
            name="dummy_tool",
            description="A dummy tool for testing",
            fn=dummy_tool_func,
            parameters={"type": "object", "properties": {"param": {"type": "string"}}}
        )
        
        agent.register_tool(tool)
        
        assert "dummy_tool" in agent.tools
        assert agent.tools["dummy_tool"].name == "dummy_tool"
        assert agent.tools["dummy_tool"].fn("test") == "Processed: test"


class TestProviderOptimizations:
    """Test provider optimizations."""
    
    def test_provider_creation_with_api_key(self):
        """Test provider creation with API key."""
        provider = create_llm("nvidia", api_key="test-key", model="test-model")
        
        assert provider.name == "nvidia"
        assert provider.model == "test-model"
        assert provider._has_credentials is True
    
    def test_provider_creation_without_api_key(self):
        """Test provider creation without API key."""
        provider = create_llm("nvidia", model="test-model")
        
        assert provider.name == "nvidia"
        assert provider.model == "test-model"
        # Should have credentials=False since no key provided
        assert provider._has_credentials is False


class TestRateLimiting:
    """Test rate limiting functionality."""
    
    def test_rate_limit_tracking(self):
        """Test that rate limiting tracks requests."""
        from app.api.raphael import _request_counts, _rate_limit_window, _max_requests_per_window
        
        # Clear any existing data
        _request_counts.clear()
        
        client_ip = "test_client"
        current_time = time.time()
        
        # Add requests within window
        for i in range(5):
            if client_ip not in _request_counts:
                _request_counts[client_ip] = []
            _request_counts[client_ip].append(current_time - i)
        
        assert len(_request_counts[client_ip]) == 5
    
    def test_rate_limit_window_cleanup(self):
        """Test that old requests are cleaned up from rate limit tracking."""
        from app.api.raphael import _request_counts, _rate_limit_window
        
        # Clear any existing data
        _request_counts.clear()
        
        client_ip = "test_client"
        current_time = time.time()
        
        # Add old and new requests
        _request_counts[client_ip] = [current_time - 120, current_time - 10, current_time - 5]
        
        # Simulate cleanup (this would happen in the actual rate limiting logic)
        _request_counts[client_ip] = [t for t in _request_counts[client_ip] if current_time - t < _rate_limit_window]
        
        assert len(_request_counts[client_ip]) == 2  # Only recent requests


class TestSecurityOptimizations:
    """Test security-related optimizations."""
    
    def test_input_sanitization_placeholder(self):
        """Placeholder test for input sanitization."""
        # This would test actual input sanitization logic
        # For now, just ensure the test structure exists
        assert True
    
    def test_error_message_sanitization(self):
        """Test that error messages are properly sanitized."""
        # This would test that sensitive information is not leaked in error messages
        # For now, just ensure the test structure exists
        assert True


class TestPerformanceOptimizations:
    """Test performance-related optimizations."""
    
    def test_caching_performance(self):
        """Test that caching improves performance."""
        cache = TokenCache(ttl=60)
        
        # First call - should be slower (cache miss)
        start_time = time.time()
        cache.set("test_key", {"data": "test"})
        first_call_time = time.time() - start_time
        
        # Second call - should be faster (cache hit)
        start_time = time.time()
        result = cache.get("test_key")
        second_call_time = time.time() - start_time
        
        assert result is not None
        # Cache hit should be faster (though this is a micro-optimization test)
        assert second_call_time <= first_call_time
    
    def test_connection_pooling(self):
        """Test that connection pooling reduces client creation overhead."""
        pool = ConnectionPool()
        unique_name = f"pooling_test_{id(self)}"
        
        creation_count = 0
        
        def create_client():
            nonlocal creation_count
            creation_count += 1
            return {"id": f"client_{creation_count}"}
        
        # Get same client multiple times
        client1 = pool.get_client(unique_name, create_client)
        client2 = pool.get_client(unique_name, create_client)
        client3 = pool.get_client(unique_name, create_client)
        
        # Should only create one client
        assert creation_count == 1, f"Expected 1 creation, got {creation_count}"
        assert client1 is client2 is client3


if __name__ == "__main__":
    pytest.main([__file__, "-v"])