from fastapi import Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db.models import Document


class DocumentRepository:
    def __init__(self, db: Session = Depends(get_db)):
        self.db = db

    def add_document(self, document: Document) -> None:
        self.db.add(document)

    def get_document(self, document_id: int, project_id: int) -> Document | None:
        return (
            self.db.query(Document)
            .filter(Document.id == document_id, Document.project_id == project_id)
            .first()
        )

    def list_project_documents(self, project_id: int) -> list[Document]:
        return self.db.query(Document).filter(Document.project_id == project_id).all()

    def get_total_project_size(self, project_id: int) -> int:
        # .scalar() returns the single value, defaults to 0 if no files exist
        size = (
            self.db.query(func.sum(Document.file_size))
            .filter(Document.project_id == project_id)
            .scalar()
        )
        return size or 0

    def delete_document(self, document: Document) -> None:
        self.db.delete(document)
