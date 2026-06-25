def test_create_artifact(client):
    resp = client.post("/projects/", json={"name": "Test Project"})
    project_id = resp.json()["id"]

    resp = client.post(
        f"/projects/{project_id}/artifacts",
        json={"type": "note", "title": "My note", "content": "Some content"},
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["type"] == "note"
    assert data["title"] == "My note"
    assert data["content"] == "Some content"
    assert data["project_id"] == project_id
    assert "id" in data
    assert "created_at" in data
    assert "updated_at" in data


def test_create_artifact_project_not_found(client):
    resp = client.post("/projects/999/artifacts", json={"type": "note", "title": "T", "content": "C"})
    assert resp.status_code == 404


def test_create_artifact_invalid_type(client):
    resp = client.post("/projects/", json={"name": "Test Project"})
    project_id = resp.json()["id"]

    resp = client.post(
        f"/projects/{project_id}/artifacts",
        json={"type": "invalid", "title": "T", "content": "C"},
    )
    assert resp.status_code == 422


def test_list_artifacts(client):
    resp = client.post("/projects/", json={"name": "Test Project"})
    project_id = resp.json()["id"]

    client.post(f"/projects/{project_id}/artifacts", json={"type": "note", "title": "A", "content": "C1"})
    client.post(f"/projects/{project_id}/artifacts", json={"type": "summary", "title": "B", "content": "C2"})

    resp = client.get(f"/projects/{project_id}/artifacts")
    assert resp.status_code == 200
    assert len(resp.json()) == 2


def test_list_artifacts_project_not_found(client):
    resp = client.get("/projects/999/artifacts")
    assert resp.status_code == 404


def test_get_artifact(client):
    resp = client.post("/projects/", json={"name": "Test Project"})
    project_id = resp.json()["id"]

    resp = client.post(f"/projects/{project_id}/artifacts", json={"type": "design", "title": "Arch", "content": "Design doc"})
    artifact_id = resp.json()["id"]

    resp = client.get(f"/artifacts/{artifact_id}")
    assert resp.status_code == 200
    assert resp.json()["title"] == "Arch"


def test_get_artifact_not_found(client):
    resp = client.get("/artifacts/999")
    assert resp.status_code == 404


def test_update_artifact(client):
    resp = client.post("/projects/", json={"name": "Test Project"})
    project_id = resp.json()["id"]

    resp = client.post(f"/projects/{project_id}/artifacts", json={"type": "note", "title": "Original", "content": "Original content"})
    artifact_id = resp.json()["id"]

    resp = client.put(
        f"/artifacts/{artifact_id}",
        json={"title": "Updated", "type": "research", "content": "Updated content"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["title"] == "Updated"
    assert data["type"] == "research"
    assert data["content"] == "Updated content"


def test_update_artifact_not_found(client):
    resp = client.put("/artifacts/999", json={"title": "Nope"})
    assert resp.status_code == 404


def test_delete_artifact(client):
    resp = client.post("/projects/", json={"name": "Test Project"})
    project_id = resp.json()["id"]

    resp = client.post(f"/projects/{project_id}/artifacts", json={"type": "note", "title": "T", "content": "C"})
    artifact_id = resp.json()["id"]

    resp = client.delete(f"/artifacts/{artifact_id}")
    assert resp.status_code == 204

    resp = client.get(f"/artifacts/{artifact_id}")
    assert resp.status_code == 404


def test_delete_artifact_not_found(client):
    resp = client.delete("/artifacts/999")
    assert resp.status_code == 404


def test_artifact_project_relationship(client):
    resp = client.post("/projects/", json={"name": "Test Project"})
    project_id = resp.json()["id"]

    resp = client.post(f"/projects/{project_id}/artifacts", json={"type": "note", "title": "A", "content": "C1"})
    assert resp.status_code == 201
    resp = client.post(f"/projects/{project_id}/artifacts", json={"type": "summary", "title": "B", "content": "C2"})
    assert resp.status_code == 201

    resp = client.get(f"/projects/{project_id}/artifacts")
    assert len(resp.json()) == 2

    resp = client.get("/projects/999/artifacts")
    assert resp.status_code == 404
