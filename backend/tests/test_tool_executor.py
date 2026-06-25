from app.services.agents import agent_registry
from app.services.tool_executor import ToolExecutor, TOOL_ROUTING


def test_list_available_tools(db_session):
    executor = ToolExecutor(db_session)
    tools = executor.list_available_tools()
    assert "memory.get_project_context" in tools
    assert "memory.get_project_summary" in tools
    assert "memory.get_active_work" in tools
    assert "search.search_project" in tools
    assert len(tools) == 4


def test_validate_tool(db_session):
    executor = ToolExecutor(db_session)
    assert executor.validate_tool("memory.get_project_context") is True
    assert executor.validate_tool("nonexistent") is False


def test_execute_memory_tool(db_session, client):
    resp = client.post("/projects/", json={"name": "Test Project"})
    project_id = resp.json()["id"]

    executor = ToolExecutor(db_session)
    result = executor.execute("memory.get_project_context", project_id=project_id)
    assert result["success"] is True
    assert result["tool"] == "memory.get_project_context"
    assert result["result"]["project"]["name"] == "Test Project"
    assert result["result"]["tasks"] == []


def test_execute_search_tool(db_session, client):
    resp = client.post("/projects/", json={"name": "Test Project"})
    project_id = resp.json()["id"]

    executor = ToolExecutor(db_session)
    result = executor.execute("search.search_project", project_id=project_id, query="test")
    assert result["success"] is True
    assert result["tool"] == "search.search_project"
    assert result["result"]["total_results"] == 0


def test_execute_invalid_tool(db_session):
    executor = ToolExecutor(db_session)
    result = executor.execute("nonexistent.tool", project_id=1)
    assert result["success"] is False
    assert "not found" in result["error"]


def test_execute_registered_but_not_routed(db_session):
    executor = ToolExecutor(db_session)
    result = executor.execute("opencode.analyze_repository", project_id=1)
    assert result["success"] is False
    assert "no executor implementation" in result["error"]


def test_agent_execute_tool_permission_denied(db_session):
    agent = agent_registry.get("researcher")
    executor = ToolExecutor(db_session)
    result = agent.execute_tool("memory.get_project_context", executor, project_id=1)
    assert result["success"] is False
    assert "permission" in result["error"].lower()


def test_agent_execute_tool_success(db_session, client):
    resp = client.post("/projects/", json={"name": "Test Project"})
    project_id = resp.json()["id"]

    agent = agent_registry.get("researcher")
    executor = ToolExecutor(db_session)
    result = agent.execute_tool("search.search_project", executor, project_id=project_id, query="test")
    assert result["success"] is True
    assert result["tool"] == "search.search_project"


def test_api_agent_execute_tool(client):
    resp = client.post("/projects/", json={"name": "Test Project"})
    project_id = resp.json()["id"]

    resp = client.post(
        f"/agents/planner/tools/memory.get_project_context",
        json={"project_id": project_id},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True
    assert data["tool"] == "memory.get_project_context"


def test_api_agent_execute_tool_permission_denied(client):
    resp = client.post(
        "/agents/researcher/tools/memory.get_project_context",
        json={"project_id": 1},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is False
    assert "permission" in data["error"].lower()


def test_api_agent_execute_tool_missing_agent(client):
    resp = client.post(
        "/agents/nonexistent/tools/search.search_project",
        json={"project_id": 1},
    )
    assert resp.status_code == 404


def test_api_agent_execute_tool_missing_tool(client):
    resp = client.post(
        "/agents/planner/tools/nonexistent.tool",
        json={"project_id": 1},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is False
