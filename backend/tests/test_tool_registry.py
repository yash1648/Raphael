from app.services.tool_registry import ToolInfo, ToolRegistry, create_default_registry


def test_register_tool():
    registry = ToolRegistry()
    registry.register_tool(ToolInfo(name="test.tool", description="A test", category="memory", available=True))
    assert registry.tool_exists("test.tool")


def test_list_tools():
    registry = create_default_registry()
    tools = registry.list_tools()
    assert len(tools) == 8
    names = [t["name"] for t in tools]
    assert "memory.get_project_context" in names
    assert "memory.get_project_summary" in names
    assert "memory.get_active_work" in names
    assert "search.search_project" in names
    assert "opencode.analyze_repository" in names
    assert "opencode.search_code" in names
    assert "opencode.review_changes" in names
    assert "opencode.generate_plan" in names


def test_get_tool():
    registry = create_default_registry()
    tool = registry.get_tool("memory.get_project_context")
    assert tool is not None
    assert tool["name"] == "memory.get_project_context"
    assert tool["category"] == "memory"
    assert tool["available"] is True


def test_get_tool_not_found():
    registry = create_default_registry()
    tool = registry.get_tool("nonexistent")
    assert tool is None


def test_tool_exists():
    registry = create_default_registry()
    assert registry.tool_exists("search.search_project") is True
    assert registry.tool_exists("fake.tool") is False


def test_api_list_tools(client):
    resp = client.get("/tools")
    assert resp.status_code == 200
    data = resp.json()
    assert "tools" in data
    assert len(data["tools"]) == 8


def test_api_get_tool(client):
    resp = client.get("/tools/search.search_project")
    assert resp.status_code == 200
    data = resp.json()
    assert data["tool"]["name"] == "search.search_project"
    assert data["tool"]["category"] == "search"


def test_api_get_tool_not_found(client):
    resp = client.get("/tools/nonexistent")
    assert resp.status_code == 404


def test_opencode_tools_default_unavailable():
    registry = create_default_registry()
    for name in ["opencode.analyze_repository", "opencode.search_code", "opencode.review_changes", "opencode.generate_plan"]:
        tool = registry.get_tool(name)
        assert tool is not None
        assert tool["available"] is False
