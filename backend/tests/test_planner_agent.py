def test_planner_blocked_recommendation(client):
    resp = client.post("/projects/", json={"name": "Test Project"})
    project_id = resp.json()["id"]

    client.post(f"/projects/{project_id}/tasks", json={"title": "Fix login", "status": "blocked"})
    client.post(f"/projects/{project_id}/tasks", json={"title": "Add tests", "status": "blocked"})

    resp = client.post(f"/agents/planner/execute", json={"project_id": project_id, "objective": "assess project"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["agent"] == "planner"
    assert data["project_status"]["blocked"] == 2
    assert data["project_status"]["in_progress"] == 0
    assert data["project_status"]["completed"] == 0
    assert data["project_status"]["todo"] == 0
    assert any("blocked" in r.lower() for r in data["recommendations"])


def test_planner_in_progress_recommendation(client):
    resp = client.post("/projects/", json={"name": "Test Project"})
    project_id = resp.json()["id"]

    client.post(f"/projects/{project_id}/tasks", json={"title": "Build API", "status": "in_progress"})
    client.post(f"/projects/{project_id}/tasks", json={"title": "Write docs", "status": "in_progress"})

    resp = client.post(f"/agents/planner/execute", json={"project_id": project_id, "objective": "assess project"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["project_status"]["in_progress"] == 2
    assert any("in-progress" in r.lower() for r in data["recommendations"])


def test_planner_todo_recommendation(client):
    resp = client.post("/projects/", json={"name": "Test Project"})
    project_id = resp.json()["id"]

    client.post(f"/projects/{project_id}/tasks", json={"title": "Setup CI", "status": "todo", "priority": 5})
    client.post(f"/projects/{project_id}/tasks", json={"title": "Add logging", "status": "todo", "priority": 1})

    resp = client.post(f"/agents/planner/execute", json={"project_id": project_id, "objective": "assess project"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["project_status"]["todo"] == 2
    assert any("todo" in r.lower() for r in data["recommendations"])


def test_planner_completed_recommendation(client):
    resp = client.post("/projects/", json={"name": "Test Project"})
    project_id = resp.json()["id"]

    client.post(f"/projects/{project_id}/tasks", json={"title": "Done", "status": "completed"})

    resp = client.post(f"/agents/planner/execute", json={"project_id": project_id, "objective": "assess project"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["project_status"]["completed"] == 1
    assert any("complete" in r.lower() for r in data["recommendations"])


def test_planner_empty_project(client):
    resp = client.post("/projects/", json={"name": "Empty Project"})
    project_id = resp.json()["id"]

    resp = client.post(f"/agents/planner/execute", json={"project_id": project_id, "objective": "assess project"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["project_status"]["completed"] == 0
    assert data["project_status"]["in_progress"] == 0
    assert data["project_status"]["blocked"] == 0
    assert data["project_status"]["todo"] == 0
    assert any("complete" in r.lower() for r in data["recommendations"])


def test_planner_blocked_takes_priority_over_in_progress(client):
    resp = client.post("/projects/", json={"name": "Test Project"})
    project_id = resp.json()["id"]

    client.post(f"/projects/{project_id}/tasks", json={"title": "Blocked task", "status": "blocked"})
    client.post(f"/projects/{project_id}/tasks", json={"title": "In progress task", "status": "in_progress"})

    resp = client.post(f"/agents/planner/execute", json={"project_id": project_id, "objective": "assess project"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["project_status"]["blocked"] == 1
    assert data["project_status"]["in_progress"] == 1
    assert any("blocked" in r.lower() for r in data["recommendations"])


def test_planner_in_progress_takes_priority_over_todo(client):
    resp = client.post("/projects/", json={"name": "Test Project"})
    project_id = resp.json()["id"]

    client.post(f"/projects/{project_id}/tasks", json={"title": "In progress task", "status": "in_progress"})
    client.post(f"/projects/{project_id}/tasks", json={"title": "Todo task", "status": "todo"})

    resp = client.post(f"/agents/planner/execute", json={"project_id": project_id, "objective": "assess project"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["project_status"]["in_progress"] == 1
    assert data["project_status"]["todo"] == 1
    assert any("in-progress" in r.lower() for r in data["recommendations"])
