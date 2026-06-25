def test_continue_workflow(client):
    resp = client.post("/projects/", json={"name": "Test Project"})
    project_id = resp.json()["id"]

    client.post(f"/projects/{project_id}/tasks", json={"title": "Task A", "status": "in_progress"})
    client.post(f"/projects/{project_id}/tasks", json={"title": "Task B", "status": "todo"})

    resp = client.post(f"/workflows/continue/{project_id}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["workflow"] == "continue_project"
    assert "project_summary" in data
    assert "active_work" in data
    assert "health" in data
    assert "next_action" in data
    assert data["project_summary"]["project_name"] == "Test Project"


def test_summary_workflow(client):
    resp = client.post("/projects/", json={"name": "Test Project"})
    project_id = resp.json()["id"]

    client.post(f"/projects/{project_id}/tasks", json={"title": "Task A", "status": "todo"})

    resp = client.get(f"/workflows/summary/{project_id}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["workflow"] == "summarize_project"
    assert "context" in data
    assert "summary" in data
    assert data["summary"]["project_name"] == "Test Project"
    assert len(data["context"]["tasks"]) == 1


def test_review_workflow(client):
    resp = client.post("/projects/", json={"name": "Test Project"})
    project_id = resp.json()["id"]

    client.post(f"/projects/{project_id}/tasks", json={"title": "Blocked task", "status": "blocked", "priority": 5})
    client.post(f"/projects/{project_id}/tasks", json={"title": "Todo task", "status": "todo", "priority": 3})
    client.post(f"/projects/{project_id}/tasks", json={"title": "Done task", "status": "completed"})

    resp = client.get(f"/workflows/review/{project_id}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["workflow"] == "review_project"
    assert "health" in data
    assert "blocked_tasks" in data
    assert "prioritized_tasks" in data
    assert len(data["blocked_tasks"]) == 1
    assert data["blocked_tasks"][0]["title"] == "Blocked task"
    assert data["prioritized_tasks"][0]["title"] == "Blocked task"


def test_continue_workflow_empty_project(client):
    resp = client.post("/projects/", json={"name": "Empty Project"})
    project_id = resp.json()["id"]

    resp = client.post(f"/workflows/continue/{project_id}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["health"]["status"] == "complete"
    assert data["next_action"]["action"] == "no_action_needed"


def test_workflow_project_not_found(client):
    resp = client.post("/workflows/continue/999")
    assert resp.status_code == 404

    resp = client.get("/workflows/summary/999")
    assert resp.status_code == 404

    resp = client.get("/workflows/review/999")
    assert resp.status_code == 404


def test_health_propagation(client):
    resp = client.post("/projects/", json={"name": "Test Project"})
    project_id = resp.json()["id"]

    client.post(f"/projects/{project_id}/tasks", json={"title": "B1", "status": "blocked"})

    resp = client.post(f"/workflows/continue/{project_id}")
    data = resp.json()
    assert data["health"]["status"] == "blocked"

    resp = client.get(f"/workflows/review/{project_id}")
    data = resp.json()
    assert data["health"]["status"] == "blocked"


def test_recommendation_propagation(client):
    resp = client.post("/projects/", json={"name": "Test Project"})
    project_id = resp.json()["id"]

    client.post(f"/projects/{project_id}/tasks", json={"title": "IP1", "status": "in_progress"})

    resp = client.post(f"/workflows/continue/{project_id}")
    data = resp.json()
    assert data["next_action"]["action"] == "finish_in_progress"

    client.post(f"/projects/{project_id}/tasks", json={"title": "B1", "status": "blocked"})

    resp = client.post(f"/workflows/continue/{project_id}")
    data = resp.json()
    assert data["next_action"]["action"] == "resolve_blockers"


def test_review_prioritization(client):
    resp = client.post("/projects/", json={"name": "Test Project"})
    project_id = resp.json()["id"]

    client.post(f"/projects/{project_id}/tasks", json={"title": "Low todo", "status": "todo", "priority": 1})
    client.post(f"/projects/{project_id}/tasks", json={"title": "High todo", "status": "todo", "priority": 10})

    resp = client.get(f"/workflows/review/{project_id}")
    data = resp.json()
    assert data["prioritized_tasks"][0]["title"] == "High todo"
    assert data["prioritized_tasks"][1]["title"] == "Low todo"
