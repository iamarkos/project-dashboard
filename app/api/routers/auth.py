from typing import Any

from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm

from app.api.schemas import UserCreate, UserResponse
from app.services.auth_service import AuthService

router = APIRouter(tags=["Authentication"])


@router.post("/auth", response_model=UserResponse)
def create_user(user: UserCreate, service: AuthService = Depends()) -> Any:
    return service.register_user(user_in=user)


@router.post("/login")
def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(), service: AuthService = Depends()
) -> dict[str, str]:
    return service.authenticate_user(username=form_data.username, password=form_data.password)
