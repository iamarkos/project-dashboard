from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException, status

from app.api.schemas import DocumentUpdate
from app.db.models import Document, User
from app.services.document_service import DocumentService


@pytest.fixture
def document_service():
    return DocumentService(
        document_repo=MagicMock(),
    )


def test_upload_document_success(document_service, mocker):
    user = User(id=1)

    mock_file = MagicMock()
    mock_file.filename = "test.pdf"
    mock_file.content_type = "application/pdf"
    mock_file.file.tell.return_value = 1024 * 1024  # 1 MB file

    document_service.document_repo.get_total_project_size.return_value = 0

    # Mock settings and cloud storage functions
    mocker.patch("app.services.document_service.settings.MAX_PROJECT_SIZE_MB", 10)
    mocker.patch("app.services.document_service.settings.MINIO_BUCKET_NAME", "test-bucket")
    mocker.patch(
        "app.services.document_service.upload_file_to_storage", return_value="path/to/test.pdf"
    )

    document_service.document_repo.add_document.side_effect = lambda doc: doc

    document = document_service.upload_document(project_id=1, current_user=user, file=mock_file)

    assert document.filename == "test.pdf"
    assert document.file_size == 1024 * 1024
    document_service.document_repo.add_document.assert_called_once()


def test_upload_document_size_limit_exceeded(document_service, mocker):
    user = User(id=1)

    mock_file = MagicMock()
    mock_file.filename = "test.pdf"
    mock_file.content_type = "application/pdf"
    mock_file.file.tell.return_value = 6 * 1024 * 1024  # 6 MB file

    # Current size is 5MB, Max is 10MB. 5 + 6 = 11MB (Exceeds limit)
    document_service.document_repo.get_total_project_size.return_value = 5 * 1024 * 1024
    mocker.patch("app.services.document_service.settings.MAX_PROJECT_SIZE_MB", 10)

    with pytest.raises(ValueError) as exc:
        document_service.upload_document(project_id=1, current_user=user, file=mock_file)

    assert "Upload rejected" in str(exc.value)


def test_get_download_url_success(document_service, mocker):
    mock_doc = Document(id=1, file_path="path/to/test.pdf")
    document_service.document_repo.get_document.return_value = mock_doc

    mocker.patch("app.services.document_service.settings.MINIO_BUCKET_NAME", "test-bucket")
    mocker.patch(
        "app.services.document_service.generate_presigned_url",
        return_value="https://minio.link/test.pdf",
    )

    result = document_service.get_download_url(project_id=1, document_id=1)

    assert result["download_url"] == "https://minio.link/test.pdf"


def test_get_download_url_not_found(document_service):
    document_service.document_repo.get_document.return_value = None

    with pytest.raises(ValueError) as exc:
        document_service.get_download_url(project_id=1, document_id=99)

    assert "Document not found" in str(exc.value)


def test_delete_document_success(document_service, mocker):
    mock_doc = Document(id=1, file_path="path/to/test.pdf")
    document_service.document_repo.get_document.return_value = mock_doc

    mocker.patch("app.services.document_service.settings.MINIO_BUCKET_NAME", "test-bucket")
    mock_delete = mocker.patch("app.services.document_service.delete_file")

    document_service.delete_document(project_id=1, document_id=1)

    mock_delete.assert_called_once_with("test-bucket", "path/to/test.pdf")
    document_service.document_repo.delete_document.assert_called_once_with(mock_doc)


def test_list_documents(document_service):
    mock_docs = [Document(id=1), Document(id=2)]
    document_service.document_repo.list_project_documents.return_value = mock_docs

    docs = document_service.list_documents(project_id=1)
    assert len(docs) == 2


def test_get_download_url_minio_failure(document_service, mocker):
    mock_doc = Document(id=1, file_path="path/to/test.pdf")
    document_service.document_repo.get_document.return_value = mock_doc

    mocker.patch("app.services.document_service.settings.MINIO_BUCKET_NAME", "test-bucket")
    # Simulate MinIO failing to generate the URL by returning None
    mocker.patch("app.services.document_service.generate_presigned_url", return_value=None)

    with pytest.raises(RuntimeError) as exc:
        document_service.get_download_url(project_id=1, document_id=1)
    assert "Could not generate" in str(exc.value)


def test_update_document_success(document_service):
    mock_doc = Document(id=1, filename="old.pdf")
    document_service.document_repo.get_document.return_value = mock_doc

    update_data = DocumentUpdate(filename="new.pdf")

    document_service.document_repo.update_document.return_value = Document(id=1, filename="new.pdf")

    updated = document_service.update_document(
        project_id=1, document_id=1, document_update=update_data
    )
    assert updated.filename == "new.pdf"


def test_update_document_not_found(document_service):
    document_service.document_repo.get_document.return_value = None
    update_data = DocumentUpdate(filename="new.pdf")

    with pytest.raises(ValueError) as exc:
        document_service.update_document(project_id=1, document_id=99, document_update=update_data)
    assert "Document not found" in str(exc.value)


def test_delete_document_not_found(document_service):
    document_service.document_repo.get_document.return_value = None

    with pytest.raises(ValueError) as exc:
        document_service.delete_document(project_id=1, document_id=99)
    assert "Document not found" in str(exc.value)


def test_delete_document_storage_failure(document_service, mocker):
    mock_doc = Document(id=1, file_path="path/to/test.pdf")
    document_service.document_repo.get_document.return_value = mock_doc

    mocker.patch("app.services.document_service.settings.MINIO_BUCKET_NAME", "test-bucket")

    # Simulate delete_file throwing a generic exception
    mocker.patch(
        "app.services.document_service.delete_file", side_effect=Exception("MinIO Offline")
    )

    with pytest.raises(RuntimeError) as exc:
        document_service.delete_document(project_id=1, document_id=1)
    assert "Failed to delete file" in str(exc.value)
