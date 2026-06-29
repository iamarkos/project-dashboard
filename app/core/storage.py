import uuid
from typing import BinaryIO

import boto3
from botocore.exceptions import ClientError
from fastapi import HTTPException, status

from app.core.config import settings

# Pulling directly from the .env variables injected by Docker Compose
MINIO_ENDPOINT = settings.MINIO_ENDPOINT
MINIO_ACCESS_KEY = settings.MINIO_ROOT_USER
MINIO_SECRET_KEY = settings.MINIO_ROOT_PASSWORD
BUCKET_NAME = settings.MINIO_BUCKET_NAME

# Initialize the S3 client pointing to our local MinIO
s3_client = boto3.client(
    "s3",
    endpoint_url=MINIO_ENDPOINT,
    aws_access_key_id=MINIO_ACCESS_KEY,
    aws_secret_access_key=MINIO_SECRET_KEY,
    region_name="us-east-1",
)


def ensure_bucket_exists() -> None:
    """
    Checks if the bucket exists in MinIO.
    If it throws a 404 Not Found error, it creates the bucket automatically.
    """
    try:
        s3_client.head_bucket(Bucket=BUCKET_NAME)
    except ClientError as e:
        error_code = e.response["Error"]["Code"]
        if error_code == "404":
            s3_client.create_bucket(Bucket=BUCKET_NAME)
            print(f"Bucket '{BUCKET_NAME}' created successfully.")
        else:
            print(f"Unexpected error checking bucket: {e}")


def upload_file_to_storage(file_obj: BinaryIO, bucket_name: str, original_filename: str) -> str:
    """
    Streams a file object directly to MinIO and returns the unique storage key.
    """
    ensure_bucket_exists()
    
    file_extension = original_filename.split(".")[-1] if "." in original_filename else "bin"
    unique_filename = f"{uuid.uuid4()}.{file_extension}"

    try:
        s3_client.upload_fileobj(file_obj, bucket_name, unique_filename)
        return unique_filename

    except ClientError as e:
        print(f"Storage Error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to upload document to storage.",
        )


def generate_presigned_url(bucket_name: str, storage_key: str, expiration: int = 3600) -> str:
    """
    Generates a presigned URL for downloading a file from MinIO.
    """
    try:
        url = s3_client.generate_presigned_url(
            "get_object", Params={"Bucket": bucket_name, "Key": storage_key}, ExpiresIn=expiration
        )
        return str(url)
    except ClientError as e:
        print(f"Presigned URL Error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate download link.",
        )


def delete_file(bucket_name: str, storage_key: str) -> None:
    """
    Deletes an object from an S3 bucket.
    """
    try:
        s3_client.delete_object(Bucket=bucket_name, Key=storage_key)
    except ClientError as e:
        print(f"Delete Error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete document from storage.",
        )
