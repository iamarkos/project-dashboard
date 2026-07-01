from typing import Any

from fastapi import APIRouter, Depends, File, UploadFile, status

from app.api.dependencies import get_current_user, require_project_access
from app.api.schemas import DocumentBase, DocumentUpdate
from app.db.models import Project, User
from app.services.document_service import DocumentService

router = APIRouter(prefix="/projects/{project_id}/documents", tags=["Documents"])


@router.post("/", response_model=DocumentBase)
def upload_document_to_project(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    project: Project = Depends(require_project_access),
    service: DocumentService = Depends(),
) -> Any:
    return service.upload_document(project_id=project.id, current_user=current_user, file=file)


@router.get("/", response_model=list[DocumentBase])
def list_project_documents(
    project: Project = Depends(require_project_access), service: DocumentService = Depends()
) -> Any:
    return service.list_documents(project_id=project.id)


@router.get("/{document_id}/download")
def download_document(
    document_id: int,
    project: Project = Depends(require_project_access),
    service: DocumentService = Depends(),
) -> dict[str, str]:
    return service.get_download_url(project_id=project.id, document_id=document_id)


@router.put("/{document_id}", response_model=DocumentBase)
def update_document(
    document_id: int,
    document_update: DocumentUpdate,
    project: Project = Depends(require_project_access),
    service: DocumentService = Depends(),
) -> Any:
    return service.update_document(
        project_id=project.id, document_id=document_id, document_update=document_update
    )


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_document(
    document_id: int,
    project: Project = Depends(require_project_access),
    service: DocumentService = Depends(),
) -> None:
    service.delete_document(project_id=project.id, document_id=document_id)
    return
