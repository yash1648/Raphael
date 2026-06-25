def test_create_session(client):
    resp = client.post("/projects/", json={"name": "Test Project"})
    project_id = resp.json()["id"]

    resp = client.post(
        f"/projects/{project_id}/sessions",
        json={
            "goal": "Build task management",
            "summary": "Added endpoints and validation",
            "actions_taken": "Added Task model",
            "unresolved_items": "Need session tracking",
        },
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["goal"] == "Build task management"
    assert data["summary"] == "Added endpoints and validation"
    assert data["actions_taken"] == "Added Task model"
    assert data["unresolved_items"] == "Need session tracking"
    assert data["project_id"] == project_id
    assert "id" in data
    assert "created_at" in data


def test_create_session_project_not_found(client):
    resp = client.post("/projects/999/sessions", json={"goal": "Test goal"})
    assert resp.status_code == 404


def test_list_sessions(client):
    resp = client.post("/projects/", json={"name": "Test Project"})
    project_id = resp.json()["id"]

    client.post(f"/projects/{project_id}/sessions", json={"goal": "Session 1"})
    client.post(f"/projects/{project_id}/sessions", json={"goal": "Session 2"})

    resp = client.get(f"/projects/{project_id}/sessions")
    assert resp.status_code == 200
    assert len(resp.json()) == 2


def test_list_sessions_project_not_found(client):
    resp = client.get("/projects/999/sessions")
    assert resp.status_code == 404


def test_get_session(client):
    resp = client.post("/projects/", json={"name": "Test Project"})
    project_id = resp.json()["id"]

    resp = client.post(f"/projects/{project_id}/sessions", json={"goal": "My Session"})
    session_id = resp.json()["id"]

    resp = client.get(f"/sessions/{session_id}")
    assert resp.status_code == 200
    assert resp.json()["goal"] == "My Session"


def test_get_session_not_found(client):
    resp = client.get("/sessions/999")
    assert resp.status_code == 404


def test_update_session(client):
    resp = client.post("/projects/", json={"name": "Test Project"})
    project_id = resp.json()["id"]

    resp = client.post(f"/projects/{project_id}/sessions", json={"goal": "Original goal"})
    session_id = resp.json()["id"]

    resp = client.put(
        f"/sessions/{session_id}",
        json={
            "goal": "Updated goal",
            "summary": "Completed work",
            "actions_taken": "Fixed bugs",
            "unresolved_items": "None",
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["goal"] == "Updated goal"
    assert data["summary"] == "Completed work"
    assert data["actions_taken"] == "Fixed bugs"
    assert data["unresolved_items"] == "None"


def test_update_session_not_found(client):
    resp = client.put("/sessions/999", json={"goal": "Nope"})
    assert resp.status_code == 404


def test_delete_session(client):
    resp = client.post("/projects/", json={"name": "Test Project"})
    project_id = resp.json()["id"]

    resp = client.post(f"/projects/{project_id}/sessions", json={"goal": "My Session"})
    session_id = resp.json()["id"]

    resp = client.delete(f"/sessions/{session_id}")
    assert resp.status_code == 204

    resp = client.get(f"/sessions/{session_id}")
    assert resp.status_code == 404


def test_delete_session_not_found(client):
    resp = client.delete("/sessions/999")
    assert resp.status_code == 404


def test_session_project_relationship(client):
    resp = client.post("/projects/", json={"name": "Test Project"})
    project_id = resp.json()["id"]

    resp = client.post(f"/projects/{project_id}/sessions", json={"goal": "Session 1"})
    assert resp.status_code == 201
    resp = client.post(f"/projects/{project_id}/sessions", json={"goal": "Session 2"})
    assert resp.status_code == 201

    resp = client.get(f"/projects/{project_id}/sessions")
    assert len(resp.json()) == 2

    resp = client.get("/projects/999/sessions")
    assert resp.status_code == 404
