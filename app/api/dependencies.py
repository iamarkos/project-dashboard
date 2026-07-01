from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jwt.exceptions import InvalidTokenError

from app.core.security import decode_access_token
from app.db.models import Project, User
from app.repositories.participant_repository import ParticipantRepository
from app.repositories.project_repository import ProjectRepository
from app.repositories.user_repository import UserRepository

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")


def get_current_user(
    token: str = Depends(oauth2_scheme), user_repo: UserRepository = Depends()
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
    project_repo: ProjectRepository = Depends(),
    participant_repo: ParticipantRepository = Depends(),
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
    project_repo: ProjectRepository = Depends(),
    participant_repo: ParticipantRepository = Depends(),
) -> Project:
    project = project_repo.get_by_id(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    if not participant_repo.is_owner(project.id, current_user.id):
        raise HTTPException(status_code=403, detail="Only project owners can perform this action.")

    return project
