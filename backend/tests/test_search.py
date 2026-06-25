def test_search_tasks(client):
    resp = client.post("/projects/", json={"name": "Test Project"})
    project_id = resp.json()["id"]

    client.post(f"/projects/{project_id}/tasks", json={"title": "Implement login", "description": "OAuth flow"})
    client.post(f"/projects/{project_id}/tasks", json={"title": "Fix logout", "description": "Session bug"})

    resp = client.get(f"/projects/{project_id}/search?q=login")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["tasks"]) == 1
    assert data["tasks"][0]["title"] == "Implement login"
    assert data["total_results"] == 1


def test_search_sessions(client):
    resp = client.post("/projects/", json={"name": "Test Project"})
    project_id = resp.json()["id"]

    client.post(f"/projects/{project_id}/sessions", json={"goal": "Build auth", "summary": "Implemented JWT"})
    client.post(f"/projects/{project_id}/sessions", json={"goal": "Fix bugs", "actions_taken": "Fixed login bug"})

    resp = client.get(f"/projects/{project_id}/search?q=JWT")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["sessions"]) == 1
    assert data["sessions"][0]["goal"] == "Build auth"


def test_search_artifacts(client):
    resp = client.post("/projects/", json={"name": "Test Project"})
    project_id = resp.json()["id"]

    client.post(f"/projects/{project_id}/artifacts", json={"type": "note", "title": "API Design", "content": "RESTful endpoints"})
    client.post(f"/projects/{project_id}/artifacts", json={"type": "research", "title": "DB Schema", "content": "SQLAlchemy models"})

    resp = client.get(f"/projects/{project_id}/search?q=RESTful")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["artifacts"]) == 1
    assert data["artifacts"][0]["title"] == "API Design"


def test_search_across_types(client):
    resp = client.post("/projects/", json={"name": "Test Project"})
    project_id = resp.json()["id"]

    client.post(f"/projects/{project_id}/tasks", json={"title": "Auth module", "description": "Login flow"})
    client.post(f"/projects/{project_id}/sessions", json={"goal": "Auth work", "summary": "Built login"})
    client.post(f"/projects/{project_id}/artifacts", json={"type": "note", "title": "Auth notes", "content": "OAuth details"})

    resp = client.get(f"/projects/{project_id}/search?q=auth")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["tasks"]) == 1
    assert len(data["sessions"]) == 1
    assert len(data["artifacts"]) == 1
    assert data["total_results"] == 3


def test_search_empty_query(client):
    resp = client.post("/projects/", json={"name": "Test Project"})
    project_id = resp.json()["id"]

    resp = client.get(f"/projects/{project_id}/search?q=")
    assert resp.status_code == 400

    resp = client.get(f"/projects/{project_id}/search")
    assert resp.status_code == 400


def test_search_missing_project(client):
    resp = client.get("/projects/999/search?q=test")
    assert resp.status_code == 404


def test_search_no_results(client):
    resp = client.post("/projects/", json={"name": "Test Project"})
    project_id = resp.json()["id"]

    resp = client.get(f"/projects/{project_id}/search?q=zzzznotfound")
    assert resp.status_code == 200
    data = resp.json()
    assert data["tasks"] == []
    assert data["sessions"] == []
    assert data["artifacts"] == []
    assert data["total_results"] == 0


def test_search_case_insensitive(client):
    resp = client.post("/projects/", json={"name": "Test Project"})
    project_id = resp.json()["id"]

    client.post(f"/projects/{project_id}/tasks", json={"title": "Login Page", "description": "Implement login"})
    client.post(f"/projects/{project_id}/tasks", json={"title": "Logout", "description": "Implement logout"})

    resp = client.get(f"/projects/{project_id}/search?q=LOGIN")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["tasks"]) == 1
    assert data["tasks"][0]["title"] == "Login Page"
