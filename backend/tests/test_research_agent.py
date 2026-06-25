def test_research_search_tasks(client):
    resp = client.post("/projects/", json={"name": "Test Project"})
    project_id = resp.json()["id"]

    client.post(f"/projects/{project_id}/tasks", json={"title": "Implement login", "description": "OAuth flow"})
    client.post(f"/projects/{project_id}/tasks", json={"title": "Fix logout", "description": "Session bug"})

    resp = client.post(f"/agents/researcher/execute", json={"project_id": project_id, "objective": "login"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["agent"] == "researcher"
    assert data["statistics"]["tasks"] == 1
    assert data["statistics"]["total"] == 1
    assert data["results"]["tasks"][0]["title"] == "Implement login"


def test_research_search_sessions(client):
    resp = client.post("/projects/", json={"name": "Test Project"})
    project_id = resp.json()["id"]

    client.post(f"/projects/{project_id}/sessions", json={"goal": "Build auth", "summary": "Implemented JWT"})

    resp = client.post(f"/agents/researcher/execute", json={"project_id": project_id, "objective": "auth"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["statistics"]["sessions"] == 1
    assert data["results"]["sessions"][0]["goal"] == "Build auth"


def test_research_search_artifacts(client):
    resp = client.post("/projects/", json={"name": "Test Project"})
    project_id = resp.json()["id"]

    client.post(f"/projects/{project_id}/artifacts", json={"type": "note", "title": "API Design", "content": "RESTful"})

    resp = client.post(f"/agents/researcher/execute", json={"project_id": project_id, "objective": "API"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["statistics"]["artifacts"] == 1
    assert data["results"]["artifacts"][0]["title"] == "API Design"


def test_research_mixed_search(client):
    resp = client.post("/projects/", json={"name": "Test Project"})
    project_id = resp.json()["id"]

    client.post(f"/projects/{project_id}/tasks", json={"title": "Auth module", "description": "Login flow"})
    client.post(f"/projects/{project_id}/sessions", json={"goal": "Auth work", "summary": "Built login"})
    client.post(f"/projects/{project_id}/artifacts", json={"type": "note", "title": "Auth notes", "content": "OAuth"})

    resp = client.post(f"/agents/researcher/execute", json={"project_id": project_id, "objective": "auth"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["statistics"]["tasks"] == 1
    assert data["statistics"]["sessions"] == 1
    assert data["statistics"]["artifacts"] == 1
    assert data["statistics"]["total"] == 3


def test_research_empty_results(client):
    resp = client.post("/projects/", json={"name": "Test Project"})
    project_id = resp.json()["id"]

    client.post(f"/projects/{project_id}/tasks", json={"title": "Something unrelated"})

    resp = client.post(f"/agents/researcher/execute", json={"project_id": project_id, "objective": "zzzznotfound"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["statistics"]["total"] == 0
    assert data["summary"] == "No project information matched the query."


def test_research_statistics(client):
    resp = client.post("/projects/", json={"name": "Test Project"})
    project_id = resp.json()["id"]

    client.post(f"/projects/{project_id}/tasks", json={"title": "Task 1"})
    client.post(f"/projects/{project_id}/tasks", json={"title": "Task 2"})
    client.post(f"/projects/{project_id}/artifacts", json={"type": "note", "title": "Note 1", "content": "C1"})

    resp = client.post(f"/agents/researcher/execute", json={"project_id": project_id, "objective": "task"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["statistics"]["tasks"] >= 2
    assert data["statistics"]["artifacts"] >= 0
    assert data["statistics"]["total"] == data["statistics"]["tasks"] + data["statistics"]["sessions"] + data["statistics"]["artifacts"]


def test_research_summary_generation(client):
    resp = client.post("/projects/", json={"name": "Test Project"})
    project_id = resp.json()["id"]

    client.post(f"/projects/{project_id}/tasks", json={"title": "Fix auth bug"})
    client.post(f"/projects/{project_id}/artifacts", json={"type": "research", "title": "Auth research", "content": "OAuth details"})
    client.post(f"/projects/{project_id}/artifacts", json={"type": "note", "title": "Another note", "content": "More auth"})

    resp = client.post(f"/agents/researcher/execute", json={"project_id": project_id, "objective": "auth"})
    assert resp.status_code == 200
    data = resp.json()
    assert "auth" in data["summary"].lower()
    assert "1" in data["summary"] or "2" in data["summary"] or "3" in data["summary"]


def test_research_invalid_project(client):
    resp = client.post("/agents/researcher/execute", json={"project_id": 999, "objective": "test"})
    assert resp.status_code == 404
