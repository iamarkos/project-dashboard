from typing import Any

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status

from app.api.dependencies import get_current_user, require_project_access, get_document_service
from app.api.schemas import DocumentBase, DocumentUpdate
from app.db.models import Project, User
from app.services.document_service import DocumentService

router = APIRouter(tags=["Documents"])


@router.post("/", response_model=DocumentBase)
def upload_document_to_project(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    project: Project = Depends(require_project_access),
    service: DocumentService = Depends(get_document_service),
) -> Any:
    try:
        return service.upload_document(project_id=project.id, current_user=current_user, file=file)
    except ValueError as e:
        if "Upload rejected" in str(e):
            raise HTTPException(status_code=status.HTTP_413_CONTENT_TOO_LARGE, detail=str(e))
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/", response_model=list[DocumentBase])
def list_project_documents(
    project: Project = Depends(require_project_access), service: DocumentService = Depends(get_document_service)
) -> Any:
    return service.list_documents(project_id=project.id)


@router.get("/{document_id}/download")
def download_document(
    document_id: int,
    project: Project = Depends(require_project_access),
    service: DocumentService = Depends(get_document_service),
) -> dict[str, str]:
    try:
        return service.get_download_url(project_id=project.id, document_id=document_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.put("/{document_id}", response_model=DocumentBase)
def update_document(
    document_id: int,
    document_update: DocumentUpdate,
    project: Project = Depends(require_project_access),
    service: DocumentService = Depends(get_document_service),
) -> Any:
    try:
        return service.update_document(
            project_id=project.id, document_id=document_id, document_update=document_update
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_document(
    document_id: int,
    project: Project = Depends(require_project_access),
    service: DocumentService = Depends(get_document_service),
) -> None:
    try:
        service.delete_document(project_id=project.id, document_id=document_id)
        return
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
