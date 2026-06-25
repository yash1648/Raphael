def test_context_aggregation(client):
    resp = client.post("/projects/", json={"name": "Test Project"})
    project_id = resp.json()["id"]

    client.post(f"/projects/{project_id}/tasks", json={"title": "Task B", "priority": 1})
    client.post(f"/projects/{project_id}/tasks", json={"title": "Task A", "priority": 5})

    client.post(f"/projects/{project_id}/sessions", json={"goal": "Session 1"})
    client.post(f"/projects/{project_id}/sessions", json={"goal": "Session 2"})

    client.post(f"/projects/{project_id}/artifacts", json={"type": "note", "title": "Note 1", "content": "C1"})
    client.post(f"/projects/{project_id}/artifacts", json={"type": "summary", "title": "Summary 1", "content": "C2"})

    resp = client.get(f"/projects/{project_id}/context")
    assert resp.status_code == 200
    data = resp.json()

    assert data["project"]["name"] == "Test Project"
    assert len(data["tasks"]) == 2
    assert data["tasks"][0]["title"] == "Task A"
    assert len(data["recent_sessions"]) == 2
    assert {s["goal"] for s in data["recent_sessions"]} == {"Session 1", "Session 2"}
    assert len(data["recent_artifacts"]) == 2
    assert {a["title"] for a in data["recent_artifacts"]} == {"Note 1", "Summary 1"}


def test_context_project_not_found(client):
    resp = client.get("/projects/999/context")
    assert resp.status_code == 404


def test_summary_generation(client):
    resp = client.post("/projects/", json={"name": "Test Project"})
    project_id = resp.json()["id"]

    client.post(f"/projects/{project_id}/tasks", json={"title": "Task 1", "status": "todo"})
    client.post(f"/projects/{project_id}/tasks", json={"title": "Task 2", "status": "in_progress"})
    client.post(f"/projects/{project_id}/tasks", json={"title": "Task 3", "status": "blocked"})
    client.post(f"/projects/{project_id}/tasks", json={"title": "Task 4", "status": "completed"})
    client.post(f"/projects/{project_id}/tasks", json={"title": "Task 5", "status": "todo"})

    client.post(f"/projects/{project_id}/sessions", json={"goal": "Goal A"})
    client.post(f"/projects/{project_id}/sessions", json={"goal": "Goal B"})

    client.post(f"/projects/{project_id}/artifacts", json={"type": "note", "title": "Note 1", "content": "C"})
    client.post(f"/projects/{project_id}/artifacts", json={"type": "research", "title": "Research 1", "content": "C"})

    resp = client.get(f"/projects/{project_id}/summary")
    assert resp.status_code == 200
    data = resp.json()

    assert data["project_name"] == "Test Project"
    assert data["task_counts"]["todo"] == 2
    assert data["task_counts"]["in_progress"] == 1
    assert data["task_counts"]["blocked"] == 1
    assert data["task_counts"]["completed"] == 1
    assert "Goal B" in data["recent_goals"]
    assert "Goal A" in data["recent_goals"]
    assert "Research 1" in data["recent_artifacts"]
    assert data["last_activity"] != ""


def test_summary_project_not_found(client):
    resp = client.get("/projects/999/summary")
    assert resp.status_code == 404


def test_active_work(client):
    resp = client.post("/projects/", json={"name": "Test Project"})
    project_id = resp.json()["id"]

    client.post(f"/projects/{project_id}/tasks", json={"title": "Active 1", "status": "in_progress", "priority": 3})
    client.post(f"/projects/{project_id}/tasks", json={"title": "Active 2", "status": "in_progress", "priority": 1})
    client.post(f"/projects/{project_id}/tasks", json={"title": "Blocked 1", "status": "blocked", "priority": 5})
    client.post(f"/projects/{project_id}/tasks", json={"title": "Todo 1", "status": "todo"})

    client.post(f"/projects/{project_id}/sessions", json={"goal": "Latest session"})
    client.post(f"/projects/{project_id}/artifacts", json={"type": "note", "title": "Latest artifact", "content": "C"})

    resp = client.get(f"/projects/{project_id}/active-work")
    assert resp.status_code == 200
    data = resp.json()

    assert len(data["in_progress_tasks"]) == 2
    assert data["in_progress_tasks"][0]["title"] == "Active 1"
    assert data["in_progress_tasks"][0]["priority"] == 3
    assert len(data["blocked_tasks"]) == 1
    assert data["blocked_tasks"][0]["title"] == "Blocked 1"
    assert data["latest_session"]["goal"] == "Latest session"
    assert data["latest_artifact"]["title"] == "Latest artifact"


def test_active_work_project_not_found(client):
    resp = client.get("/projects/999/active-work")
    assert resp.status_code == 404


def test_empty_project_handling(client):
    resp = client.post("/projects/", json={"name": "Empty Project"})
    project_id = resp.json()["id"]

    resp = client.get(f"/projects/{project_id}/context")
    assert resp.status_code == 200
    assert resp.json()["tasks"] == []
    assert resp.json()["recent_sessions"] == []
    assert resp.json()["recent_artifacts"] == []

    resp = client.get(f"/projects/{project_id}/summary")
    assert resp.status_code == 200
    data = resp.json()
    assert data["task_counts"]["todo"] == 0
    assert data["recent_goals"] == []
    assert data["recent_artifacts"] == []

    resp = client.get(f"/projects/{project_id}/active-work")
    assert resp.status_code == 200
    data = resp.json()
    assert data["in_progress_tasks"] == []
    assert data["blocked_tasks"] == []
    assert data["latest_session"] is None
    assert data["latest_artifact"] is None
