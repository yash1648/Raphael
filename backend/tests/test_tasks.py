def test_create_task(client):
    resp = client.post("/projects/", json={"name": "Test Project"})
    project = resp.json()
    project_id = project["id"]

    resp = client.post(f"/projects/{project_id}/tasks", json={"title": "My Task"})
    assert resp.status_code == 201
    data = resp.json()
    assert data["title"] == "My Task"
    assert data["description"] == ""
    assert data["status"] == "todo"
    assert data["priority"] == 0
    assert data["project_id"] == project_id
    assert "id" in data
    assert "created_at" in data
    assert "updated_at" in data


def test_create_task_project_not_found(client):
    resp = client.post("/projects/999/tasks", json={"title": "Task"})
    assert resp.status_code == 404


def test_list_tasks(client):
    resp = client.post("/projects/", json={"name": "Test Project"})
    project_id = resp.json()["id"]

    client.post(f"/projects/{project_id}/tasks", json={"title": "Task 1"})
    client.post(f"/projects/{project_id}/tasks", json={"title": "Task 2"})

    resp = client.get(f"/projects/{project_id}/tasks")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 2


def test_list_tasks_project_not_found(client):
    resp = client.get("/projects/999/tasks")
    assert resp.status_code == 404


def test_get_task(client):
    resp = client.post("/projects/", json={"name": "Test Project"})
    project_id = resp.json()["id"]

    resp = client.post(f"/projects/{project_id}/tasks", json={"title": "My Task"})
    task_id = resp.json()["id"]

    resp = client.get(f"/tasks/{task_id}")
    assert resp.status_code == 200
    assert resp.json()["title"] == "My Task"


def test_get_task_not_found(client):
    resp = client.get("/tasks/999")
    assert resp.status_code == 404


def test_update_task(client):
    resp = client.post("/projects/", json={"name": "Test Project"})
    project_id = resp.json()["id"]

    resp = client.post(f"/projects/{project_id}/tasks", json={"title": "My Task"})
    task_id = resp.json()["id"]

    resp = client.put(
        f"/tasks/{task_id}",
        json={"title": "Updated", "status": "in_progress", "priority": 3},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["title"] == "Updated"
    assert data["status"] == "in_progress"
    assert data["priority"] == 3


def test_update_task_not_found(client):
    resp = client.put("/tasks/999", json={"title": "Nope"})
    assert resp.status_code == 404


def test_complete_task(client):
    resp = client.post("/projects/", json={"name": "Test Project"})
    project_id = resp.json()["id"]

    resp = client.post(f"/projects/{project_id}/tasks", json={"title": "My Task"})
    task_id = resp.json()["id"]

    resp = client.put(f"/tasks/{task_id}", json={"status": "completed"})
    assert resp.status_code == 200
    assert resp.json()["status"] == "completed"


def test_delete_task(client):
    resp = client.post("/projects/", json={"name": "Test Project"})
    project_id = resp.json()["id"]

    resp = client.post(f"/projects/{project_id}/tasks", json={"title": "My Task"})
    task_id = resp.json()["id"]

    resp = client.delete(f"/tasks/{task_id}")
    assert resp.status_code == 204

    resp = client.get(f"/tasks/{task_id}")
    assert resp.status_code == 404


def test_delete_task_not_found(client):
    resp = client.delete("/tasks/999")
    assert resp.status_code == 404


def test_validate_status(client):
    resp = client.post("/projects/", json={"name": "Test Project"})
    project_id = resp.json()["id"]

    resp = client.post(f"/projects/{project_id}/tasks", json={"title": "Task", "status": "invalid"})
    assert resp.status_code == 422


def test_task_project_relationship(client):
    resp = client.post("/projects/", json={"name": "Test Project"})
    project_id = resp.json()["id"]

    resp = client.post(f"/projects/{project_id}/tasks", json={"title": "Task 1"})
    assert resp.status_code == 201
    resp = client.post(f"/projects/{project_id}/tasks", json={"title": "Task 2"})
    assert resp.status_code == 201

    resp = client.get(f"/projects/{project_id}/tasks")
    assert len(resp.json()) == 2

    resp = client.get("/projects/999/tasks")
    assert resp.status_code == 404
