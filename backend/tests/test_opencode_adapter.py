from app.services import OpenCodeAdapter


def test_adapter_instantiation():
    adapter = OpenCodeAdapter()
    assert isinstance(adapter, OpenCodeAdapter)


def test_analyze_repository_format():
    adapter = OpenCodeAdapter()
    result = adapter.analyze_repository(project_id=1, repo_path="/repo", objective="understand arch")
    assert result["status"] == "not_implemented"
    assert result["action"] == "analyze_repository"
    assert result["project_id"] == 1
    assert result["repo_path"] == "/repo"
    assert result["objective"] == "understand arch"


def test_search_code_format():
    adapter = OpenCodeAdapter()
    result = adapter.search_code(project_id=2, repo_path="/repo", query="find bugs")
    assert result["status"] == "not_implemented"
    assert result["action"] == "search_code"
    assert result["project_id"] == 2
    assert result["repo_path"] == "/repo"
    assert result["query"] == "find bugs"


def test_review_changes_format():
    adapter = OpenCodeAdapter()
    result = adapter.review_changes(project_id=3, repo_path="/repo")
    assert result["status"] == "not_implemented"
    assert result["action"] == "review_changes"
    assert result["project_id"] == 3
    assert result["repo_path"] == "/repo"


def test_generate_plan_format():
    adapter = OpenCodeAdapter()
    result = adapter.generate_plan(project_id=4, objective="build feature")
    assert result["status"] == "not_implemented"
    assert result["action"] == "generate_plan"
    assert result["project_id"] == 4
    assert result["objective"] == "build feature"


def test_health_endpoint(client):
    resp = client.get("/health/opencode")
    assert resp.status_code == 200
    data = resp.json()
    assert data["available"] is False
    assert data["status"] == "adapter_ready"
