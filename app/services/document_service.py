from pathlib import Path

from fastapi import UploadFile

from app.api.schemas import DocumentUpdate
from app.core.config import settings
from app.core.storage import delete_file, generate_presigned_url, upload_file_to_storage
from app.db.models import Document, User
from app.repositories.document_repository import DocumentRepository

ALLOWED_EXTENSIONS = {".pdf", ".docx"}
ALLOWED_MIME_TYPES = {
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
}


class DocumentService:
    def __init__(
        self,
        document_repo: DocumentRepository,
    ):
        self.document_repo = document_repo

    def upload_document(self, project_id: int, current_user: User, file: UploadFile) -> Document:

        # Check file type
        extension = Path(str(file.filename)).suffix.lower()
        if extension not in ALLOWED_EXTENSIONS or file.content_type not in ALLOWED_MIME_TYPES:
            raise ValueError("Only PDF and DOCX files are allowed.")

        # Read the file size in bytes
        file.file.seek(0, 2)
        file_size = file.file.tell()
        file.file.seek(0)

        # Check Size Limit
        current_total_size = self.document_repo.get_total_project_size(project_id)
        max_bytes = settings.MAX_PROJECT_SIZE_MB * 1024 * 1024

        if current_total_size + file_size > max_bytes:
            current_mb = current_total_size / (1024 * 1024)
            raise ValueError(
                f"Upload rejected. Project storage limit is {settings.MAX_PROJECT_SIZE_MB} \
                    MB. Current usage: {current_mb:.2f}MB."
            )

        # Upload to MinIO
        filename = file.filename or "unnamed_document.bin"
        file_path = upload_file_to_storage(file.file, settings.MINIO_BUCKET_NAME, filename)

        # Save to Database
        new_document = Document(
            project_id=project_id,
            created_by=current_user.id,
            filename=filename,
            file_path=file_path,
            file_size=file_size,
        )

        return self.document_repo.add_document(new_document)

    def list_documents(self, project_id: int) -> list[Document]:
        return self.document_repo.list_project_documents(project_id)

    def get_download_url(self, project_id: int, document_id: int) -> dict[str, str]:
        document = self.document_repo.get_document(document_id, project_id)
        if not document:
            raise ValueError("Document not found in this project.")

        url = generate_presigned_url(settings.MINIO_BUCKET_NAME, str(document.file_path))
        if not url:
            raise RuntimeError("Could not generate download link.")

        return {"download_url": url}

    def update_document(
        self, project_id: int, document_id: int, document_update: DocumentUpdate
    ) -> Document:
        document = self.document_repo.get_document(document_id, project_id)
        if not document:
            raise ValueError("Document not found in this project.")

        return self.document_repo.update_document(document, document_update.filename)

    def delete_document(self, project_id: int, document_id: int) -> None:
        document = self.document_repo.get_document(document_id, project_id)
        if not document:
            raise ValueError("Document not found in this project.")

        try:
            delete_file(settings.MINIO_BUCKET_NAME, str(document.file_path))
        except Exception:
            raise RuntimeError("Failed to delete file from storage.")

        self.document_repo.delete_document(document)
