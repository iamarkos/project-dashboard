import boto3
import uuid
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
    region_name="us-east-1"
)

def ensure_bucket_exists():
    """
    Checks if the bucket exists in MinIO. 
    If it throws a 404 Not Found error, it creates the bucket automatically.
    """
    try:
        s3_client.head_bucket(Bucket=BUCKET_NAME)
    except ClientError as e:
        error_code = e.response['Error']['Code']
        if error_code == '404':
            s3_client.create_bucket(Bucket=BUCKET_NAME)
            print(f"Bucket '{BUCKET_NAME}' created successfully.")
        else:
            print(f"Unexpected error checking bucket: {e}")

# Execute the check immediately when FastAPI imports this file
ensure_bucket_exists()


def upload_file_to_storage(file_obj, original_filename: str) -> str:
    """
    Streams a file object directly to MinIO and returns the unique storage key.
    """
    file_extension = original_filename.split(".")[-1] if "." in original_filename else "bin"
    unique_filename = f"{uuid.uuid4()}.{file_extension}"

    try:
        s3_client.upload_fileobj(
            file_obj,
            BUCKET_NAME,
            unique_filename
        )
        return unique_filename
        
    except ClientError as e:
        print(f"Storage Error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to upload document to storage."
        )