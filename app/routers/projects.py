from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.db.database import SessionLocal
from app.models.models import Project, ProjectParticipant, Role, User
from app.schemas.schemas import ProjectCreate, ProjectResponse, ProjectUpdate, ProjectInvite, ProjectInviteResponse
from app.dependencies import get_current_user, get_db

router = APIRouter(prefix="/projects", tags=["Projects"])

@router.post("/", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
def create_project(
    project_in: ProjectCreate, 
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user)
):
    # 1. Ensure the "Owner" role exists in the database
    owner_role = db.query(Role).filter(Role.name == "Owner").first()
    if not owner_role:
        owner_role = Role(name="Owner")
        db.add(owner_role)
        db.commit()
        db.refresh(owner_role)

    # 2. Create the Project
    new_project = Project(
        title=project_in.title,
        description=project_in.description,
        created_by=current_user.id
    )
    db.add(new_project)
    db.commit()
    db.refresh(new_project)

    # 3. Create the Participant linking the user, project, and role
    participant = ProjectParticipant(
        project_id=new_project.id,
        user_id=current_user.id,
        role_id=owner_role.id
    )
    db.add(participant)
    db.commit()

    return new_project

@router.get("/", response_model=List[ProjectResponse])
def get_user_projects(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Fetch projects where the current user is a participant
    projects = (
        db.query(Project)
        .join(ProjectParticipant)
        .filter(ProjectParticipant.user_id == current_user.id)
        .all()
    )
    return projects

@router.get("/{project_id}", response_model=ProjectResponse)
def get_project(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Fetch the project and ensure the current user is a participant
    project = (
        db.query(Project)
        .join(ProjectParticipant)
        .filter(Project.id == project_id, ProjectParticipant.user_id == current_user.id)
        .first()
    )
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found or you do not have access."
        )
    return project

@router.patch("/{project_id}", response_model=ProjectResponse)
def update_project(
    project_id: int,
    project_in: ProjectUpdate,  # You might want to create a separate schema for updates
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Fetch the project and ensure the current user is a participant
    project = (
        db.query(Project)
        .join(ProjectParticipant)
        .filter(Project.id == project_id, ProjectParticipant.user_id == current_user.id)
        .first()
    )
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found or you do not have access."
        )

    update_data = project_in.model_dump(exclude_unset=True)
    # Apply updates
    for key, value in update_data.items():
        setattr(project, key, value)

    db.commit()
    db.refresh(project)

    return project

@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_project(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    participant = (
        db.query(ProjectParticipant)
        .join(Role)
        .filter(
            ProjectParticipant.project_id == project_id,
            ProjectParticipant.user_id == current_user.id
        )
        .first()
    )

    # 1. Check if they are even a part of the project
    if not participant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found or you do not have access."
        )
        
    # 2. Check if they have the Owner role
    if participant.role.name != "Owner":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the project owner can delete this project."
        )

    # 3. Delete the actual project (CASCADE handles the rest)
    db.delete(participant.project)
    db.commit()
    
    return # 204 requires no response body

@router.post("/{project_id}/invite", response_model=ProjectInviteResponse)
def invite_user_to_project(
    project_id: int,
    invite_in: ProjectInvite,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # 1. Ensure the current user is the owner of the project
    participant = (
        db.query(ProjectParticipant)
        .join(Role)
        .filter(
            ProjectParticipant.project_id == project_id,
            ProjectParticipant.user_id == current_user.id
        )
        .first()
    )

    if not participant or participant.role.name != "Owner":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the project owner can invite users."
        )

    # 2. Ensure the user to be invited exists
    user_to_invite = db.query(User).filter(User.id == invite_in.user_id).first()
    if not user_to_invite:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User to invite not found."
        )

    # 3. Ensure the role exists
    role = db.query(Role).filter(Role.id == invite_in.role_id).first()
    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Role not found."
        )

    # 4. Check if the user is already a participant in the project
    existing_participant = (
        db.query(ProjectParticipant)
        .filter(
            ProjectParticipant.project_id == project_id,
            ProjectParticipant.user_id == invite_in.user_id
        )
        .first()
    )
    if existing_participant:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User is already a participant in this project."
        )

    # 5. Create the new participant entry
    new_participant = ProjectParticipant(
        project_id=project_id,
        user_id=invite_in.user_id,
        role_id=invite_in.role_id
    )
    db.add(new_participant)
    db.commit()
    #db.refresh(new_participant)

    return ProjectInviteResponse(
        project_id=project_id,
        user_id=invite_in.user_id,
        role_id=invite_in.role_id,
        role_name=str(role.name)
    )