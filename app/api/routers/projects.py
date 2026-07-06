from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.dependencies import get_current_user, require_project_access
from app.api.schemas import (
    ProjectCreate,
    ProjectInvite,
    ProjectInviteResponse,
    ProjectResponse,
    ProjectUpdate,
)
from app.db.models import Project, User
from app.services.project_service import ProjectService
from app.api.dependencies import get_project_service
router = APIRouter(tags=["Projects"])


@router.post("/", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
def create_project(
    project_in: ProjectCreate,
    current_user: User = Depends(get_current_user),
    service: ProjectService = Depends(get_project_service),
) -> Any:
    try:
        return service.create_project(
            owner=current_user, title=project_in.title, description=str(project_in.description)
        )
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/", response_model=list[ProjectResponse])
def get_user_projects(
    current_user: User = Depends(get_current_user), service: ProjectService = Depends(get_project_service)
) -> Any:
    return service.get_projects(current_user)


@router.get("/{project_id}", response_model=ProjectResponse)
def get_project(
    project: Project = Depends(require_project_access),
) -> Any:
    return project


@router.patch("/{project_id}", response_model=ProjectResponse)
def update_project(
    project_id: int,
    project_in: ProjectUpdate,
    current_user: User = Depends(get_current_user),
    service: ProjectService = Depends(get_project_service),
) -> Any:
    try:
        return service.update_project(
            project_id=project_id, current_user=current_user, project_in=project_in
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_project(
    project_id: int,
    current_user: User = Depends(get_current_user),
    service: ProjectService = Depends(get_project_service),
) -> None:
    try:
        service.delete_project(project_id=project_id, current_user=current_user)
        return
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))


@router.post("/{project_id}/invite", response_model=ProjectInviteResponse)
def invite_user_to_project(
    project_id: int,
    invite_in: ProjectInvite,
    current_user: User = Depends(get_current_user),
    service: ProjectService = Depends(get_project_service),
) -> Any:
    try:
        return service.invite_user(
            project_id=project_id, current_user=current_user, invite_in=invite_in
        )
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except ValueError as e:
        error_msg = str(e)
        if "not found" in error_msg.lower():
            raise HTTPException(status_code=404, detail=error_msg)
        raise HTTPException(status_code=400, detail=error_msg)