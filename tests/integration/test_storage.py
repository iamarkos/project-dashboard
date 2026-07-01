from unittest.mock import MagicMock, patch

import pytest
from botocore.exceptions import ClientError
from fastapi import HTTPException

from app.core.storage import (
    BUCKET_NAME,
    delete_file,
    ensure_bucket_exists,
    generate_presigned_url,
    upload_file_to_storage,
)


# Helper to generate a fake botocore ClientError
def create_client_error(code="500"):
    return ClientError(
        {"Error": {"Code": code, "Message": "Something went wrong"}}, "OperationName"
    )


@patch("app.core.storage.s3_client")
def test_upload_file_to_storage_failure(mock_s3):
    # Setup the mock to raise ClientError when called
    mock_s3.upload_fileobj.side_effect = create_client_error()

    # Mocking file object
    file_obj = MagicMock()

    with pytest.raises(HTTPException) as exc:
        upload_file_to_storage(file_obj, "my-bucket", "test.txt")

    assert exc.value.status_code == 500
    assert "Failed to upload document" in exc.value.detail


@patch("app.core.storage.s3_client")
def test_ensure_bucket_exists_non_404_error(mock_s3):
    # Setup mock to raise a non-404 error (e.g., 500 Access Denied)
    mock_s3.head_bucket.side_effect = create_client_error(code="500")

    # This should print to console but not crash or raise HTTPException
    ensure_bucket_exists()

    # Verify print/logic was reached
    mock_s3.head_bucket.assert_called_once()


@patch("app.core.storage.s3_client")
def test_generate_presigned_url_failure(mock_s3):
    mock_s3.generate_presigned_url.side_effect = create_client_error()

    with pytest.raises(HTTPException) as exc:
        generate_presigned_url("bucket", "key")

    assert exc.value.status_code == 500


@patch("app.core.storage.s3_client")
def test_delete_file_failure(mock_s3):
    mock_s3.delete_object.side_effect = create_client_error()

    with pytest.raises(HTTPException) as exc:
        delete_file("bucket", "key")

    assert exc.value.status_code == 500


@patch("app.core.storage.s3_client")
def test_ensure_bucket_exists_creates_bucket(mock_s3):
    # Make head_bucket raise a 404 ClientError
    mock_s3.head_bucket.side_effect = ClientError(
        {"Error": {"Code": "404", "Message": "Not Found"}}, "HeadBucket"
    )

    ensure_bucket_exists()

    # Check that create_bucket was actually called
    mock_s3.create_bucket.assert_called_once_with(Bucket=BUCKET_NAME)
