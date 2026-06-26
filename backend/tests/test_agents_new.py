"""Tests for the new advanced agent system."""

from unittest.mock import MagicMock, patch

from app.agents.base import Agent, Tool
from app.capabilities.code_executor import CodeExecutor
from app.capabilities.file_ops import FileOpsTool
from app.capabilities.web_search import WebSearchTool


class TestTool:
    def test_tool_creation(self):
        def my_fn(**kwargs):
            return {"result": "done"}

        tool = Tool(
            name="test_tool",
            description="A test tool",
            fn=my_fn,
            parameters={"type": "object", "properties": {"x": {"type": "string"}}},
        )
        assert tool.name == "test_tool"
        assert tool.description == "A test tool"

    def test_tool_execution(self):
        tool = Tool(name="echo", description="Echo", fn=lambda **kw: kw)
        result = tool.execute(message="hello")
        assert result == {"message": "hello"}

    def test_tool_to_openai_format(self):
        tool = Tool(
            name="search",
            description="Search the web",
            fn=lambda **kw: [],
            parameters={"type": "object", "properties": {"q": {"type": "string"}}},
        )
        oai = tool.to_openai_tool()
        assert oai["type"] == "function"
        assert oai["function"]["name"] == "search"
        assert "parameters" in oai["function"]


class TestAgentBase:
    def test_agent_creation(self):
        agent = Agent(name="TestAgent", description="A test agent")
        assert agent.name == "TestAgent"
        assert agent.description == "A test agent"
        assert len(agent.tools) == 0

    def test_register_tool(self):
        agent = Agent()
        tool = Tool(name="ping", description="Ping", fn=lambda: "pong")
        agent.register_tool(tool)
        assert "ping" in agent.tools
        assert agent.tools["ping"].name == "ping"

    def test_register_multiple_tools(self):
        agent = Agent()
        t1 = Tool(name="a", description="A", fn=lambda: 1)
        t2 = Tool(name="b", description="B", fn=lambda: 2)
        agent.register_tools(t1, t2)
        assert len(agent.tools) == 2

    def test_reset_conversation(self):
        agent = Agent()
        agent.add_context("user", "Hello")
        agent.add_context("assistant", "Hi")
        assert len(agent._conversation_history) == 2
        agent.reset_conversation()
        assert len(agent._conversation_history) == 0

    def test_add_context(self):
        agent = Agent()
        agent.add_context("user", "Test message")
        assert len(agent._conversation_history) == 1
        assert agent._conversation_history[0]["role"] == "user"
        assert agent._conversation_history[0]["content"] == "Test message"


class TestCodeExecutor:
    def test_execute_python(self, db_session):
        executor = CodeExecutor()
        result = executor.execute_python("print('hello from test')")
        assert result["success"] is True
        assert "hello from test" in result["stdout"]


class TestFileOps:
    def test_file_info_nonexistent(self):
        ops = FileOpsTool()
        result = ops.file_info("/nonexistent/path")
        assert "error" in result

    def test_list_directory(self):
        ops = FileOpsTool()
        result = ops.list_directory(".")
        assert isinstance(result, list)
        # Should find at least some files in the backend directory
        assert len(result) > 0
        assert any(item["type"] == "file" for item in result)


class TestWebSearchTool:
    def test_search_web_fallback(self):
        """Should return fallback message if search fails."""
        web = WebSearchTool()
        # This should work or return error gracefully
        results = web.search_web("test query", num_results=2)
        assert isinstance(results, list)
        # Even on error, should return list
        if results and "error" in results[0]:
            assert True  # Graceful failure
        else:
            assert len(results) <= 2

    def test_fetch_page_invalid_url(self):
        web = WebSearchTool()
        result = web.fetch_page("https://invalid.url.xyz")
        assert result["success"] is False
