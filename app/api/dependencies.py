from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jwt.exceptions import InvalidTokenError
from sqlalchemy.orm import Session

from app.core.security import decode_access_token
from app.db.database import get_db
from app.db.models import Project, User

# --- Repositories ---
from app.repositories.participant_repository import ParticipantRepository
from app.repositories.project_repository import ProjectRepository
from app.repositories.user_repository import UserRepository
from app.repositories.role_repository import RoleRepository
from app.repositories.document_repository import DocumentRepository

# --- Services ---
from app.services.auth_service import AuthService
from app.services.project_service import ProjectService
from app.services.document_service import DocumentService


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

# ==========================================
# 1. REPOSITORY FACTORIES
# ==========================================
def get_user_repo(db: Session = Depends(get_db)) -> UserRepository:
    return UserRepository(db)

def get_role_repo(db: Session = Depends(get_db)) -> RoleRepository:
    return RoleRepository(db)

def get_project_repo(db: Session = Depends(get_db)) -> ProjectRepository:
    return ProjectRepository(db)

def get_participant_repo(db: Session = Depends(get_db)) -> ParticipantRepository:
    return ParticipantRepository(db)

def get_document_repo(db: Session = Depends(get_db)) -> DocumentRepository:
    return DocumentRepository(db)


# ==========================================
# 2. AUTH & AUTHORIZATION DEPENDENCIES
# ==========================================
def get_current_user(
    token: str = Depends(oauth2_scheme), 
    user_repo: UserRepository = Depends(get_user_repo)  
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = decode_access_token(token)
        user_id = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except InvalidTokenError:
        raise credentials_exception

    user = user_repo.get_user_by_id(int(user_id))
    if user is None:
        raise credentials_exception
    return user


def require_project_access(
    project_id: int,
    current_user: User = Depends(get_current_user),
    project_repo: ProjectRepository = Depends(get_project_repo),
    participant_repo: ParticipantRepository = Depends(get_participant_repo), 
) -> Project:
    project = project_repo.get_by_id(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    if not participant_repo.has_access(project.id, current_user.id):
        raise HTTPException(status_code=403, detail="Access denied")

    return project


def require_owner(
    project_id: int,
    current_user: User = Depends(get_current_user),
    project_repo: ProjectRepository = Depends(get_project_repo), 
    participant_repo: ParticipantRepository = Depends(get_participant_repo),
) -> Project:
    project = project_repo.get_by_id(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    if not participant_repo.is_owner(project.id, current_user.id):
        raise HTTPException(status_code=403, detail="Only project owners can perform this action.")

    return project


# ==========================================
# 3. SERVICE FACTORIES
# ==========================================
def get_auth_service(
    user_repo: UserRepository = Depends(get_user_repo),
    role_repo: RoleRepository = Depends(get_role_repo)
) -> AuthService:
    return AuthService(user_repo=user_repo, role_repo=role_repo)

def get_project_service(
    project_repo: ProjectRepository = Depends(get_project_repo),
    participant_repo: ParticipantRepository = Depends(get_participant_repo),
    user_repo: UserRepository = Depends(get_user_repo),
    role_repo: RoleRepository = Depends(get_role_repo)
) -> ProjectService:
    return ProjectService(
        project_repo=project_repo, 
        participant_repo=participant_repo,
        user_repo=user_repo,
        role_repo=role_repo
    )

def get_document_service(
    document_repo: DocumentRepository = Depends(get_document_repo)
) -> DocumentService:
    return DocumentService(document_repo=document_repo)