from typing import Any

from fastapi import APIRouter, Depends, status

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

router = APIRouter(prefix="/projects", tags=["Projects"])


@router.post("/", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
def create_project(
    project_in: ProjectCreate,
    current_user: User = Depends(get_current_user),
    service: ProjectService = Depends(),
) -> Any:
    return service.create_project(
        owner=current_user, title=project_in.title, description=str(project_in.description)
    )


@router.get("/", response_model=list[ProjectResponse])
def get_user_projects(
    current_user: User = Depends(get_current_user), service: ProjectService = Depends()
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
    service: ProjectService = Depends(),
) -> Any:
    return service.update_project(
        project_id=project_id, current_user=current_user, project_in=project_in
    )


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_project(
    project_id: int,
    current_user: User = Depends(get_current_user),
    service: ProjectService = Depends(),
) -> None:
    service.delete_project(project_id=project_id, current_user=current_user)
    return


@router.post("/{project_id}/invite", response_model=ProjectInviteResponse)
def invite_user_to_project(
    project_id: int,
    invite_in: ProjectInvite,
    current_user: User = Depends(get_current_user),
    service: ProjectService = Depends(),
) -> Any:

    return service.invite_user(
        project_id=project_id, current_user=current_user, invite_in=invite_in
    )
