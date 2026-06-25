from app.services.agents import AgentRegistry, agent_registry
from app.services.agents.base_agent import BaseAgent


def test_registry_population():
    assert len(agent_registry.list_agents()) == 3


def test_list_agents():
    agents = agent_registry.list_agents()
    names = {a.name for a in agents}
    assert names == {"planner", "researcher", "architect"}


def test_lookup_planner():
    agent = agent_registry.get("planner")
    assert agent is not None
    assert agent.name == "planner"
    assert "memory.get_project_context" in agent.allowed_tools
    assert "memory.get_project_summary" in agent.allowed_tools


def test_lookup_researcher():
    agent = agent_registry.get("researcher")
    assert agent is not None
    assert agent.name == "researcher"
    assert agent.allowed_tools == ["search.search_project"]


def test_lookup_architect():
    agent = agent_registry.get("architect")
    assert agent is not None
    assert agent.name == "architect"
    assert "opencode.analyze_repository" in agent.allowed_tools
    assert "opencode.generate_plan" in agent.allowed_tools


def test_agent_not_found():
    agent = agent_registry.get("nonexistent")
    assert agent is None


class MockExecutor:
    def execute(self, tool_name, **kwargs):
        return {"tool": tool_name, "success": True, "result": {"tasks": [], "sessions": [], "artifacts": []}}

def test_execute_returns_expected_format():
    agent = agent_registry.get("researcher")
    executor = MockExecutor()
    result = agent.execute(project_id=1, objective="test objective", executor=executor)
    assert result["agent"] == "researcher"
    assert result["objective"] == "test objective"
    assert "results" in result
    assert "summary" in result


def test_api_list_agents(client):
    resp = client.get("/agents")
    assert resp.status_code == 200
    data = resp.json()
    assert "agents" in data
    assert len(data["agents"]) == 3
    names = {a["name"] for a in data["agents"]}
    assert names == {"planner", "researcher", "architect"}


def test_api_get_agent(client):
    resp = client.get("/agents/planner")
    assert resp.status_code == 200
    data = resp.json()
    assert data["agent"]["name"] == "planner"
    assert "memory.get_project_context" in data["agent"]["allowed_tools"]


def test_api_get_agent_not_found(client):
    resp = client.get("/agents/nonexistent")
    assert resp.status_code == 404


def test_api_execute_agent(client):
    resp = client.post("/projects/", json={"name": "Test Project"})
    project_id = resp.json()["id"]
    resp = client.post(
        "/agents/planner/execute",
        json={"project_id": project_id, "objective": "build feature"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["agent"] == "planner"
    assert data["objective"] == "build feature"
    assert "project_status" in data
    assert "recommendations" in data


def test_api_execute_agent_not_found(client):
    resp = client.post(
        "/agents/nonexistent/execute",
        json={"project_id": 1, "objective": "test"},
    )
    assert resp.status_code == 404


def test_register_custom_agent():
    registry = AgentRegistry()
    agent = BaseAgent()
    agent.name = "custom"
    agent.description = "Custom agent"
    agent.allowed_tools = ["search.search_project"]
    registry.register(agent)
    assert registry.agent_exists("custom")
    assert registry.get("custom").name == "custom"
