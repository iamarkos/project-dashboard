import uuid

from fastapi.testclient import TestClient

from app.db.models import ProjectParticipant


def test_create_project(client: TestClient, auth_headers: dict) -> None:
    payload = {"title": "My New Project", "description": "Project description here"}
    response = client.post("/projects", json=payload, headers=auth_headers)

    assert response.status_code in (200, 201)
    data = response.json()
    assert data["title"] == "My New Project"
    assert "id" in data


def test_get_projects_list(client: TestClient, auth_headers: dict, test_project: dict) -> None:
    response = client.get("/projects", headers=auth_headers)

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    # Ensure the project we created in the fixture is in the list
    assert any(proj["id"] == test_project["id"] for proj in data)


def test_get_project_by_id(client: TestClient, auth_headers: dict, test_project: dict) -> None:
    project_id = test_project["id"]
    response = client.get(f"/projects/{project_id}", headers=auth_headers)

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == project_id
    assert data["title"] == test_project["title"]


def test_update_project(client: TestClient, auth_headers: dict, test_project: dict) -> None:
    project_id = test_project["id"]
    update_payload = {"title": "Updated Title", "description": "Updated description"}

    response = client.patch(f"/projects/{project_id}", json=update_payload, headers=auth_headers)

    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Updated Title"
    assert data["description"] == "Updated description"


def test_delete_project(client: TestClient, auth_headers: dict, test_project: dict) -> None:
    project_id = test_project["id"]

    # 1. Delete it
    delete_response = client.delete(f"/projects/{project_id}", headers=auth_headers)
    assert delete_response.status_code in (200, 204)

    # 2. Try to fetch it again, expect a 404 Not Found
    get_response = client.get(f"/projects/{project_id}", headers=auth_headers)
    assert get_response.status_code == 404


def test_get_nonexistent_project(client: TestClient, auth_headers: dict) -> None:
    # Pass a dummy ID that will never exist
    response = client.get("/projects/999999", headers=auth_headers)
    assert response.status_code == 404


# =================================================================
# SECURITY & ACCESS CONTROL TESTS
# =================================================================


def test_access_other_user_project_forbidden(
    client: TestClient, alt_auth_headers: dict, test_project: dict
) -> None:
    # ACT: User B tries to read User A's project
    project_id = test_project["id"]
    response = client.get(f"/projects/{project_id}", headers=alt_auth_headers)

    # ASSERT: APIs usually return 403 (Forbidden) or 404 (Not Found to hide existence)
    assert response.status_code in (403, 404)


def test_delete_other_user_project_forbidden(
    client: TestClient, alt_auth_headers: dict, test_project: dict
) -> None:
    # ACT: User B tries to delete User A's project
    project_id = test_project["id"]
    response = client.delete(f"/projects/{project_id}", headers=alt_auth_headers)

    # ASSERT: Must be blocked
    assert response.status_code in (403, 404)


def test_invite_user_to_project(client: TestClient, auth_headers: dict, test_project: dict) -> None:

    unique_id = uuid.uuid4()
    auth_response = client.post(
        "/auth",
        json={
            "username": f"inv_{unique_id.hex[:8]}",
            "email": f"invitee_{unique_id}@example.com",
            "password": "password",
            "repeat_password": "password",
        },
    )
    invitee_id = auth_response.json()["id"]

    project_id = test_project["id"]
    invite_payload = {"user_id": invitee_id, "role_id": 1}  # Use ID 1 (Member)

    response = client.post(
        f"/projects/{project_id}/invite", json=invite_payload, headers=auth_headers
    )

    assert response.status_code in (200, 201)


def test_project_update_not_found(client: TestClient, auth_headers: dict) -> None:
    res = client.patch("/projects/99999", json={"title": "New Title"}, headers=auth_headers)
    assert res.status_code == 404


def test_project_delete_forbidden(
    client: TestClient, auth_headers: dict, alt_auth_headers: dict, test_project: dict
) -> None:
    # We use the alt_user (who isn't the owner)
    res = client.delete(f"/projects/{test_project['id']}", headers=alt_auth_headers)
    assert res.status_code in (403, 404)


def test_project_invite_edge_cases(
    client: TestClient, auth_headers: dict, alt_auth_headers: dict, test_project: dict
) -> None:
    project_id = test_project["id"]

    payload = {"user_id": 999, "role_id": 1}

    # Non-owner tries to invite (403)
    res = client.post(f"/projects/{project_id}/invite", json=payload, headers=alt_auth_headers)
    assert res.status_code == 403

    # User to invite does not exist (404)
    res = client.post(f"/projects/{project_id}/invite", json=payload, headers=auth_headers)
    assert res.status_code == 404


def test_invite_invalid_role(client: TestClient, auth_headers: dict, test_project: dict) -> None:
    owner_id = 1  # Update if your test owner ID is different

    # Role does not exist (404)
    res = client.post(
        f"/projects/{test_project['id']}/invite",
        json={"user_id": owner_id, "role_id": 999},
        headers=auth_headers,
    )
    assert res.status_code == 404


def test_invite_already_participant(client, auth_headers, test_project, db_session) -> None:
    # Get the first participant (the owner)
    participant = (
        db_session.query(ProjectParticipant)
        .filter(ProjectParticipant.project_id == test_project["id"])
        .first()
    )

    res = client.post(
        f"/projects/{test_project['id']}/invite",
        json={"user_id": participant.user_id, "role_id": 1},
        headers=auth_headers,
    )
    assert res.status_code == 400
