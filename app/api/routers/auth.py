from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

from app.api.dependencies import get_auth_service
from app.api.schemas import UserCreate, UserResponse
from app.services.auth_service import AuthService

router = APIRouter(tags=["Authentication"])


@router.post("/auth", response_model=UserResponse)
def create_user(user: UserCreate, service: AuthService = Depends(get_auth_service)) -> Any:
    try:
        return service.register_user(user_in=user)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/login")
def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    service: AuthService = Depends(get_auth_service),
) -> dict[str, str]:
    try:
        return service.authenticate_user(username=form_data.username, password=form_data.password)
    except PermissionError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        )
