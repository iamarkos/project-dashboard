from typing import Any

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user, get_db
from app.api.schemas import (
    DocumentBase,
    DocumentUpdate,
)
from app.core.config import settings
from app.core.storage import delete_file, generate_presigned_url, upload_file_to_storage
from app.db.models import Document, ProjectParticipant, User

router = APIRouter(prefix="/projects/{project_id}/documents", tags=["Documents"])


@router.post("/", response_model=DocumentBase)
def upload_document_to_project(
    project_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    # Ensure the current user is a participant of the project
    participant = (
        db.query(ProjectParticipant)
        .filter(
            ProjectParticipant.project_id == project_id,
            ProjectParticipant.user_id == current_user.id,
        )
        .first()
    )

    if not participant:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You must be a participant of the project to upload documents.",
        )

    # Read the file size in bytes
    file.file.seek(0, 2)  # Move cursor to the end of the file
    file_size = file.file.tell()  # Get the byte position (which equals the size)
    file.file.seek(0)  # Reset cursor back to the beginning for the upload stream

    # SIZE LIMIT CHECK
    current_total_size = (
        db.query(func.sum(Document.file_size)).filter(Document.project_id == project_id).scalar()
        or 0
    )  # .scalar() returns the single value, defaults to 0 if no files exist

    max_mb = settings.MAX_PROJECT_SIZE_MB
    max_bytes = max_mb * 1024 * 1024
    current_mb = current_total_size / (1024 * 1024)

    if current_total_size + file_size > max_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_CONTENT_TOO_LARGE,
            detail=f"Upload rejected. Project storage limit is {max_mb}MB. \
                Current usage: {current_mb:.2f}MB.",
        )

    # Upload the file to storage (MinIO)
    filename = file.filename or "unnamed_document.bin"
    file_path = upload_file_to_storage(file.file, settings.MINIO_BUCKET_NAME, filename)

    # Create a new Document entry in the database
    new_document = Document(
        project_id=project_id,
        created_by=current_user.id,
        filename=filename,
        file_path=file_path,
        file_size=file_size,
    )
    db.add(new_document)
    db.commit()
    db.refresh(new_document)

    return new_document


@router.get("/", response_model=list[DocumentBase])
def list_project_documents(
    project_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
) -> Any:
    # Ensure the current user is a participant of the project
    participant = (
        db.query(ProjectParticipant)
        .filter(
            ProjectParticipant.project_id == project_id,
            ProjectParticipant.user_id == current_user.id,
        )
        .first()
    )

    if not participant:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You must be a participant of the project to view documents.",
        )

    # Fetch all documents for the project
    documents = db.query(Document).filter(Document.project_id == project_id).all()
    return documents


@router.get("/{document_id}/download")
def download_document(
    project_id: int,
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict[str, str]:
    # Ensure the current user is a participant of the project
    participant = (
        db.query(ProjectParticipant)
        .filter(
            ProjectParticipant.project_id == project_id,
            ProjectParticipant.user_id == current_user.id,
        )
        .first()
    )

    if not participant:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You must be a participant of the project to download documents.",
        )

    # Fetch the document and ensure it belongs to the specified project
    document = (
        db.query(Document)
        .filter(Document.id == document_id, Document.project_id == project_id)
        .first()
    )

    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Document not found in this project."
        )

    # 3. Generate the Presigned URL using boto3
    url = generate_presigned_url(settings.MINIO_BUCKET_NAME, str(document.file_path))
    if not url:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not generate download link.",
        )

    return {"download_url": url}


@router.put("/{document_id}", response_model=DocumentBase)
def update_document(
    project_id: int,
    document_id: int,
    document_update: DocumentUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    # Ensure the current user is a participant of the project
    participant = (
        db.query(ProjectParticipant)
        .filter(
            ProjectParticipant.project_id == project_id,
            ProjectParticipant.user_id == current_user.id,
        )
        .first()
    )

    if not participant:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You must be a participant of the project to update documents.",
        )

    # Fetch the document and ensure it belongs to the specified project
    document = (
        db.query(Document)
        .filter(Document.id == document_id, Document.project_id == project_id)
        .first()
    )

    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Document not found in this project."
        )

    # Update the document's filename
    setattr(document, "filename", document_update.filename)

    db.commit()
    db.refresh(document)

    return document


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_document(
    project_id: int,
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    # Ensure the current user is a participant of the project
    participant = (
        db.query(ProjectParticipant)
        .filter(
            ProjectParticipant.project_id == project_id,
            ProjectParticipant.user_id == current_user.id,
        )
        .first()
    )

    if not participant:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to modify this project."
        )

    # Fetch the document and ensure it belongs to the specified project
    document = (
        db.query(Document)
        .filter(Document.id == document_id, Document.project_id == project_id)
        .first()
    )

    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Document not found in this project."
        )

    # Delete physical file from MinIO
    try:
        delete_file(settings.MINIO_BUCKET_NAME, str(document.file_path))
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete file from storage.",
        )

    # Delete the document entry from the database
    db.delete(document)
    db.commit()

    return  # 204 requires no response body
