from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.database import SessionLocal
from app.models.models import Project, ProjectParticipant, Role, User
from app.schemas.schemas import ProjectCreate, ProjectResponse
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