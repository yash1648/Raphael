def test_architect_overview_generation(client):
    resp = client.post("/projects/", json={"name": "Test Project"})
    project_id = resp.json()["id"]

    client.post(f"/projects/{project_id}/tasks", json={"title": "Task 1", "status": "in_progress"})
    client.post(f"/projects/{project_id}/sessions", json={"goal": "Sprint 1", "summary": "Work"})
    client.post(f"/projects/{project_id}/artifacts", json={"type": "note", "title": "Note 1", "content": "Content"})

    resp = client.post("/agents/architect/execute", json={"project_id": project_id, "objective": "review architecture"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["agent"] == "architect"
    assert data["project_overview"]["tasks"] >= 1
    assert data["project_overview"]["sessions"] >= 1
    assert data["project_overview"]["artifacts"] >= 1


def test_architect_recommendation_blocked(client):
    resp = client.post("/projects/", json={"name": "Test Project"})
    project_id = resp.json()["id"]

    client.post(f"/projects/{project_id}/tasks", json={"title": "Blocked task", "status": "blocked"})

    resp = client.post("/agents/architect/execute", json={"project_id": project_id, "objective": "review architecture"})
    assert resp.status_code == 200
    data = resp.json()
    assert any("blockers" in r.lower() for r in data["recommendations"])
    assert data["health"]["status"] == "blocked"


def test_architect_recommendation_active(client):
    resp = client.post("/projects/", json={"name": "Test Project"})
    project_id = resp.json()["id"]

    client.post(f"/projects/{project_id}/tasks", json={"title": "Active work", "status": "in_progress"})

    resp = client.post("/agents/architect/execute", json={"project_id": project_id, "objective": "review architecture"})
    assert resp.status_code == 200
    data = resp.json()
    assert any("stabilize" in r.lower() for r in data["recommendations"])
    assert data["health"]["status"] == "active"


def test_architect_recommendation_completed(client):
    resp = client.post("/projects/", json={"name": "Test Project"})
    project_id = resp.json()["id"]

    client.post(f"/projects/{project_id}/tasks", json={"title": "Done", "status": "completed"})

    resp = client.post("/agents/architect/execute", json={"project_id": project_id, "objective": "review architecture"})
    assert resp.status_code == 200
    data = resp.json()
    assert any("stable" in r.lower() for r in data["recommendations"])
    assert data["health"]["status"] == "complete"


def test_architect_recommendation_incremental(client):
    resp = client.post("/projects/", json={"name": "Test Project"})
    project_id = resp.json()["id"]

    client.post(f"/projects/{project_id}/tasks", json={"title": "Todo task", "status": "todo"})

    resp = client.post("/agents/architect/execute", json={"project_id": project_id, "objective": "review architecture"})
    assert resp.status_code == 200
    data = resp.json()
    assert any("incremental" in r.lower() for r in data["recommendations"])


def test_architect_opencode_stub(client):
    resp = client.post("/projects/", json={"name": "Test Project"})
    project_id = resp.json()["id"]

    resp = client.post("/agents/architect/execute", json={"project_id": project_id, "objective": "review architecture"})
    assert resp.status_code == 200
    data = resp.json()
    assert "opencode" in data
    assert data["opencode"]["status"] == "not_implemented"
    assert data["opencode"]["action"] == "generate_plan"
    assert data["opencode"]["project_id"] == project_id
    assert data["opencode"]["objective"] == "review architecture"


def test_architect_missing_project(client):
    resp = client.post("/agents/architect/execute", json={"project_id": 999, "objective": "review architecture"})
    assert resp.status_code == 404


def test_architect_response_format(client):
    resp = client.post("/projects/", json={"name": "Test Project"})
    project_id = resp.json()["id"]

    client.post(f"/projects/{project_id}/tasks", json={"title": "Task", "status": "todo"})

    resp = client.post("/agents/architect/execute", json={"project_id": project_id, "objective": "project structure"})
    assert resp.status_code == 200
    data = resp.json()
    assert set(data.keys()) == {"agent", "objective", "project_overview", "health", "opencode", "recommendations"}
    assert isinstance(data["project_overview"], dict)
    assert set(data["project_overview"].keys()) == {"tasks", "sessions", "artifacts"}
    assert isinstance(data["health"], dict)
    assert isinstance(data["opencode"], dict)
    assert isinstance(data["recommendations"], list)
