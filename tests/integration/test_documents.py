import io

import pytest
from fastapi.testclient import TestClient


def test_upload_document_success(
    client: TestClient, auth_headers: dict, test_project: dict
) -> None:
    # 1. ARRANGE: Create a dummy file in memory
    file_content = b"This is the content of the document"
    file = io.BytesIO(file_content)
    file.name = "test_document.pdf"

    project_id = test_project["id"]

    # 2. ACT: Send as multipart/form-data
    files = {"file": (file.name, file, "application/pdf")}
    response = client.post(f"/projects/{project_id}/documents", files=files, headers=auth_headers)

    # 3. ASSERT
    assert response.status_code in (200, 201)
    data = response.json()
    assert data["filename"] == "test_document.pdf"
    assert "id" in data


def test_download_document(client: TestClient, auth_headers: dict, test_project: dict) -> None:
    # Upload a document
    file = io.BytesIO(b"Hello World")
    file.name = "download_me.pdf"
    project_id = test_project["id"]
    upload_res = client.post(
        f"/projects/{project_id}/documents",
        files={"file": (file.name, file, "application/pdf")},
        headers=auth_headers,
    )
    doc_id = upload_res.json()["id"]

    # Request the download link
    response = client.get(
        f"/projects/{project_id}/documents/{doc_id}/download", headers=auth_headers
    )

    # Expect JSON with a URL
    assert response.status_code == 200
    data = response.json()

    assert "download_url" in data
    assert data["download_url"].startswith("http")

    # Verify the download URL actually works
    import httpx  # to request the pre-signed URL

    file_response = httpx.get(data["download_url"], follow_redirects=True)

    assert file_response.status_code == 200
    assert file_response.content == b"Hello World"


def test_download_document_forbidden(
    client: TestClient, auth_headers: dict, alt_auth_headers: dict, test_project: dict
) -> None:
    # The Owner (auth_headers) uploads a private document
    file = io.BytesIO(b"Top Secret Content")
    file.name = "secret_file.pdf"
    project_id = test_project["id"]

    upload_res = client.post(
        f"/projects/{project_id}/documents",
        files={"file": (file.name, file, "application/pdf")},
        headers=auth_headers,
    )
    doc_id = upload_res.json()["id"]

    # User B (alt_auth_headers) tries to access User A's project document
    response = client.get(
        f"/projects/{project_id}/documents/{doc_id}/download", headers=alt_auth_headers
    )

    assert response.status_code in (403, 404)


def test_delete_document_forbidden(
    client: TestClient, auth_headers: dict, alt_auth_headers: dict, test_project: dict
) -> None:
    # User A (Owner) uploads a document
    file = io.BytesIO(b"Crucial business data")
    file.name = "important.pdf"
    project_id = test_project["id"]

    upload_res = client.post(
        f"/projects/{project_id}/documents",
        files={"file": (file.name, file, "application/pdf")},
        headers=auth_headers,
    )
    doc_id = upload_res.json()["id"]

    # User B tries to delete it
    response = client.delete(f"/projects/{project_id}/documents/{doc_id}", headers=alt_auth_headers)

    assert response.status_code in (403, 404)


def test_upload_empty_document(client: TestClient, auth_headers: dict, test_project: dict) -> None:
    # Create a 0-byte file
    file = io.BytesIO(b"")
    file.name = "empty_file.pdf"
    project_id = test_project["id"]

    response = client.post(
        f"/projects/{project_id}/documents",
        files={"file": (file.name, file, "application/pdf")},
        headers=auth_headers,
    )

    assert response.status_code != 500


def test_project_deletion_cascades_to_documents(
    client: TestClient, auth_headers: dict, test_project: dict
) -> None:
    # Upload a document to the project
    file = io.BytesIO(b"Data to be destroyed")
    file.name = "doomed_file.pdf"
    project_id = test_project["id"]

    upload_res = client.post(
        f"/projects/{project_id}/documents",
        files={"file": (file.name, file, "application/pdf")},
        headers=auth_headers,
    )
    doc_id = upload_res.json()["id"]

    # Delete the entire project
    delete_res = client.delete(f"/projects/{project_id}", headers=auth_headers)
    assert delete_res.status_code in (200, 204)

    # The document should no longer be accessible
    download_res = client.get(
        f"/projects/{project_id}/documents/{doc_id}/download", headers=auth_headers
    )

    assert download_res.status_code in (403, 404)


def test_project_storage_limit_exceeded(
    client: TestClient, auth_headers: dict, test_project: dict, monkeypatch: pytest.MonkeyPatch
) -> None:
    # Temporarily overwrite the limit to 0 bytes for this test
    monkeypatch.setattr("app.core.config.settings.MAX_PROJECT_SIZE_MB", 0)

    file = io.BytesIO(b"This file is 38 bytes, which is greater than 0!")
    file.name = "too_big.pdf"
    project_id = test_project["id"]

    # Attempt to upload the file
    response = client.post(
        f"/projects/{project_id}/documents",
        files={"file": (file.name, file, "application/pdf")},
        headers=auth_headers,
    )

    # The server MUST reject the upload with a 413
    assert response.status_code == 413

    # Verify the custom error message is returned
    data = response.json()
    assert "Upload rejected" in data["detail"]


def test_list_documents(
    client: TestClient, auth_headers: dict, alt_auth_headers: dict, test_project: dict
) -> None:
    project_id = test_project["id"]

    # Upload a document so the list isn't empty
    file = io.BytesIO(b"Data for listing")
    file.name = "list_me.pdf"
    client.post(
        f"/projects/{project_id}/documents",
        files={"file": (file.name, file, "application/pdf")},
        headers=auth_headers,
    )

    # Happy Path (Owner can list documents)
    list_res = client.get(f"/projects/{project_id}/documents", headers=auth_headers)
    assert list_res.status_code == 200
    assert len(list_res.json()) >= 1

    # Forbidden (Non-participant blocked)
    list_forbidden = client.get(f"/projects/{project_id}/documents", headers=alt_auth_headers)
    assert list_forbidden.status_code == 403


def test_update_document(
    client: TestClient, auth_headers: dict, alt_auth_headers: dict, test_project: dict
) -> None:
    project_id = test_project["id"]

    # Upload a document to get a valid doc_id
    file = io.BytesIO(b"Data for updating")
    file.name = "original_name.pdf"
    upload_res = client.post(
        f"/projects/{project_id}/documents",
        files={"file": (file.name, file, "application/pdf")},
        headers=auth_headers,
    )
    doc_id = upload_res.json()["id"]

    # Happy Path (Owner can update)
    update_res = client.put(
        f"/projects/{project_id}/documents/{doc_id}",
        json={"filename": "new_name.pdf"},
        headers=auth_headers,
    )
    assert update_res.status_code == 200
    assert update_res.json()["filename"] == "new_name.pdf"

    # Forbidden (Non-participant blocked)
    update_forbidden = client.put(
        f"/projects/{project_id}/documents/{doc_id}",
        json={"filename": "hacked_name.pdf"},
        headers=alt_auth_headers,
    )
    assert update_forbidden.status_code == 403


def test_document_edge_cases_and_not_found(
    client: TestClient, auth_headers: dict, alt_auth_headers: dict, test_project: dict
) -> None:
    project_id = test_project["id"]
    fake_doc_id = 99999

    # 1. TEST UPLOAD FORBIDDEN
    file = io.BytesIO(b"Forbidden upload")
    file.name = "forbidden.pdf"
    upload_res = client.post(
        f"/projects/{project_id}/documents",
        files={"file": (file.name, file, "application/pdf")},
        headers=alt_auth_headers,
    )
    assert upload_res.status_code == 403

    # 2. TEST DOWNLOAD NOT FOUND
    download_res = client.get(
        f"/projects/{project_id}/documents/{fake_doc_id}/download", headers=auth_headers
    )
    assert download_res.status_code == 404

    # 3. TEST UPDATE NOT FOUND -> Covers line 180
    update_res = client.put(
        f"/projects/{project_id}/documents/{fake_doc_id}",
        json={"filename": "wont_work.pdf"},
        headers=auth_headers,
    )
    assert update_res.status_code == 404

    # 4. TEST DELETE NOT FOUND
    delete_res = client.delete(
        f"/projects/{project_id}/documents/{fake_doc_id}", headers=auth_headers
    )
    assert delete_res.status_code == 404


def test_upload_invalid_file_type(
    client: TestClient, auth_headers: dict, test_project: dict
) -> None:
    # Attempt to upload a forbidden .txt file
    file = io.BytesIO(b"This is a text file")
    file.name = "invalid_format.txt"
    project_id = test_project["id"]

    response = client.post(
        f"/projects/{project_id}/documents",
        files={"file": (file.name, file, "text/plain")},
        headers=auth_headers,
    )

    # API should reject it because it's not a pdf or docx
    assert response.status_code in (400, 422)
    assert (
        "type" in response.text.lower()
        or "format" in response.text.lower()
        or "pdf" in response.text.lower()
    )
